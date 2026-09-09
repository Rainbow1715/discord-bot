import asyncio
import random
import discord
from discord import app_commands
from discord.ext import commands
from database import get_user_profile, save_data, GACHA_POOL
from achievement import on_battle_win, on_battle_lose

# --------------------------------------------------
# 🎪 イベントステージ設定
# --------------------------------------------------
EVENT_CONFIG = {
    "name": "【特別イベント】強敵襲来！",
    "target_gacha_name": None,  # Noneならガチャプールからランダム、"キャラ名" を入れれば特定キャラ固定
    "boss_level": 100,          # ボスのレベル（Lv.100など）
    "hp_multiplier": 5.0,       # ボス用HP倍率
    "atk_multiplier": 1.2,      # ボス用攻撃力倍率
    "reward_gold": (5000, 10000),
    "reward_rainbow": (200, 500),
    "reward_exp": (200, 400),
}


# --------------------------------------------------
# ⚖️ 補助関数
# --------------------------------------------------
def create_smooth_bar(ratio, length=10):
    ratio = max(0.0, min(1.0, ratio))
    filled_length = int(length * ratio)
    if ratio > 0 and filled_length == 0:
        filled_length = 1
    filled_bar = "█" * filled_length
    empty_bar = "⬜︎" * (length - filled_length)
    return filled_bar + empty_bar


# --------------------------------------------------
# 👤 キャラクタークラス
# --------------------------------------------------
class Character:
    def __init__(self, data_dict, is_boss=False):
        self.data = data_dict
        self.name = data_dict.get("name", "謎の敵")
        self.icon = data_dict.get("icon", "👤")
        self.element = data_dict.get("element", "無")
        
        # ⚔️ 攻撃タイプ（物理 / 魔法）を追加（未設定の場合はデフォルトで「物理」）
        self.atk_type = data_dict.get("atk_type", "物理")
        
        self.level = data_dict.get("level", 1)
        self.max_hp = data_dict.get("hp", 100)
        self.hp = self.max_hp
        self.atk = data_dict.get("atk", 15)
        self.spd = data_dict.get("spd", 10)
        self.rec = data_dict.get("rec", 0)
        self.skill_name = data_dict.get("skill_name", "通常攻撃")
        self.skill_pow = data_dict.get("skill_pow", 20)
        self.skill_type = data_dict.get("skill_type", "normal")
        self.is_boss = is_boss

    def action(self, target, party, boss_state):
        # 攻撃タイプ用アイコン
        type_icon = "⚔️" if self.atk_type == "物理" else "🔮"

        # 35%の確率でスキル発動
        if random.randint(1, 100) <= 35:
            if self.skill_type == "heal_all":
                healed_names = []
                for p in party:
                    if p.hp > 0:
                        p.hp = min(p.max_hp, p.hp + int(p.max_hp * 0.5))
                        healed_names.append(p.name)
                if healed_names:
                    return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{', '.join(healed_names)}** のHPが回復した！"
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ しかし効果がなかった！"

            elif self.skill_type == "physical":
                dmg = self.skill_pow + int(self.atk * 0.5)
                target.hp = max(0, target.hp - dmg)
                return f"💥 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** に **{dmg}** ダメージ！"

            elif self.skill_type == "stun":
                boss_state["stun_turns"] = 2
                return f"🌀 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** は動揺して **2ターン行動不能** になった！"

            else:
                dmg = self.skill_pow + self.atk + random.randint(-3, 3)
                target.hp = max(0, target.hp - dmg)
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** に **{dmg}** ダメージ！"
        else:
            # 通常攻撃（物理/魔法をログに明記）
            dmg = max(1, self.atk + random.randint(-2, 2))
            target.hp = max(0, target.hp - dmg)
            return f"{type_icon} {self.icon} **{self.name}** の{self.atk_type}攻撃！ **{target.name}** に **{dmg}** ダメージ！"


# --------------------------------------------------
# ⚔️ バトル共通処理
# --------------------------------------------------
async def execute_battle(interaction: discord.Interaction, is_event: bool = False):
    u_data = get_user_profile(interaction.user.id)
    party = [Character(u_data["characters"][i]) for i in u_data["party_indices"] if i < len(u_data["characters"])]

    if not party:
        await interaction.response.send_message("❌ パーティメンバーがセットされていません。`/party` で編成してください！", ephemeral=True)
        return

    # 味方パーティの平均レベルを計算
    avg_level = sum(p.level for p in party) // len(party)

    # 👹 敵（ボス）の生成
    if is_event:
        target_name = EVENT_CONFIG.get("target_gacha_name")
        candidate = None
        if target_name:
            candidate = next((c for c in GACHA_POOL if c["name"] == target_name), None)
        if not candidate:
            candidate = random.choice(GACHA_POOL)

        boss_lvl = EVENT_CONFIG.get("boss_level", 100)
        calculated_hp = int((candidate["hp"] + (boss_lvl * 15)) * EVENT_CONFIG.get("hp_multiplier", 3.0))
        calculated_atk = int((candidate["atk"] + (boss_lvl * 3)) * EVENT_CONFIG.get("atk_multiplier", 1.0))

        boss_data = {
            "name": f"【Lv.{boss_lvl}】{candidate['name']}",
            "icon": candidate.get("icon", "👹"),
            "element": candidate.get("element", "無"),
            "atk_type": candidate.get("atk_type", random.choice(["物理", "魔法"])),  # キャラデータにあれば取得、無ければランダム
            "level": boss_lvl,
            "hp": calculated_hp,
            "atk": calculated_atk,
            "spd": candidate.get("spd", 10),
            "rec": candidate.get("rec", 0),
            "skill_name": candidate.get("skill_name", "極大攻撃"),
            "skill_pow": candidate.get("skill_pow", 50),
            "skill_type": candidate.get("skill_type", "normal")
        }
        title_name = EVENT_CONFIG["name"]
        rewards = (EVENT_CONFIG["reward_gold"], EVENT_CONFIG["reward_rainbow"], EVENT_CONFIG["reward_exp"])
    else:
        boss_lvl = max(1, avg_level)
        boss_data = {
            "name": f"【Lv.{boss_lvl}】野生のモンスター",
            "icon": "👹",
            "element": "無",
            "atk_type": random.choice(["物理", "魔法"]),
            "level": boss_lvl,
            "hp": 80 + (boss_lvl * 25),
            "atk": 10 + (boss_lvl * 4),
            "spd": 10,
            "rec": 0,
            "skill_name": "なぎ払い",
            "skill_pow": 15 + (boss_lvl * 2),
            "skill_type": "normal"
        }
        title_name = "通常クエスト"
        rewards = ((1000, 3000), (50, 100), (50, 100))

    boss = Character(boss_data, is_boss=True)

    # メンバー表示に [物理/魔法] の表記を追加
    party_desc = ', '.join([f"**{p.name}** [{p.atk_type}] (Lv.{p.level})" for p in party])

    embed = discord.Embed(
        title=f"⚔️ {title_name} 開始！",
        description=f"立ちはだかる敵: **{boss.name}** [{boss.atk_type}]\n出撃メンバー: {party_desc}",
        color=0xE74C3C if is_event else 0x3498DB,
    )
    await interaction.response.send_message(embed=embed)
    battle_msg = await interaction.original_response()

    turn = 1
    logs = []
    boss_state = {"stun_turns": 0}

    # バトル進行ループ
    while boss.hp > 0 and any(p.hp > 0 for p in party):
        await asyncio.sleep(1.8)
        turn_log = f"**--- ターン {turn} ---**\n"

        # 味方の攻撃
        for p in party:
            if p.hp > 0 and boss.hp > 0:
                turn_log += p.action(boss, party, boss_state) + "\n"

        # ボスの攻撃
        if boss.hp > 0:
            if boss_state["stun_turns"] > 0:
                turn_log += f"💫 **{boss.name}** は動けない！（残り {boss_state['stun_turns']} ターン）\n"
                boss_state["stun_turns"] -= 1
            else:
                alive_party = [p for p in party if p.hp > 0]
                if alive_party:
                    target = random.choice(alive_party)
                    turn_log += boss.action(target, party, boss_state) + "\n"

        logs.append(turn_log)
        if len(logs) > 2:
            logs.pop(0)

        boss_bar = create_smooth_bar(boss.hp / boss.max_hp)
        status_text = f"\n{boss.icon} **{boss.name}**: HP {boss.hp}/{boss.max_hp} {boss_bar}\n"

        for p in party:
            p_bar = create_smooth_bar(p.hp / p.max_hp)
            status_text += f"{p.icon} **{p.name}**: HP {p.hp}/{p.max_hp} {p_bar}\n"

        new_embed = discord.Embed(
            title=f"⚔️ バトル進行中... (ターン {turn})",
            description="\n".join(logs) + status_text,
            color=0xFF9900,
        )
        await battle_msg.edit(embed=new_embed)
        turn += 1

    # 結末判定
    await asyncio.sleep(1.0)
    if boss.hp <= 0:
        # --------------------------------------------------
        # 🏆 勝利処理
        # --------------------------------------------------
        (g_min, g_max), (r_min, r_max), (e_min, e_max) = rewards
        gold_gained = random.randint(g_min, g_max)
        rainbow_gained = random.randint(r_min, r_max)
        exp_gained = random.randint(e_min, e_max)

        u_data["gold"] = u_data.get("gold", 0) + gold_gained
        u_data["items"]["虹の欠片"] = u_data["items"].get("虹の欠片", 0) + rainbow_gained

        # 🏆 勝利実績チェック
        await on_battle_win(interaction, u_data)

        lvl_up_msgs = []
        for p in party:
            c_data = p.data
            c_data["exp"] = c_data.get("exp", 0) + exp_gained
            
            while True:
                next_exp = c_data["level"] * 100
                if c_data["exp"] >= next_exp:
                    c_data["exp"] -= next_exp
                    c_data["level"] += 1
                    c_data["hp"] += 8
                    c_data["atk"] += 3
                    if f"🎉 **{c_data['name']}**" not in "".join(lvl_up_msgs):
                        lvl_up_msgs.append(f"🎉 **{c_data['name']}** (Lv.{c_data['level']} にUP!)")
                else:
                    break

        save_data()
        lvl_str = "\n" + "\n".join(lvl_up_msgs) if lvl_up_msgs else ""

        result_embed = discord.Embed(
            title="🎉 VICTORY!",
            description=(
                f"**{boss.name}** を撃破した！\n\n"
                f"💰 **獲得金**: {gold_gained} G\n"
                f"💎 **獲得虹の欠片**: {rainbow_gained} 個\n"
                f"✨ **獲得経験値**: 出撃メンバー全員に {exp_gained} EXP"
                f"{lvl_str}"
            ),
            color=0x00FF00,
        )

    else:
        # --------------------------------------------------
        # 💀 敗北処理
        # --------------------------------------------------
        await on_battle_lose(interaction, u_data)
        save_data()

        result_embed = discord.Embed(
            title="💀 GAME OVER...",
            description="全滅してしまった...",
            color=0xFF0000,
        )

    # メッセージを更新して最終結果を表示
    await battle_msg.edit(embed=result_embed)


# --------------------------------------------------
# 💬 Cog（コマンド登録）
# --------------------------------------------------
class BattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="battle", description="通常のクエストバトルを行います（味方のレベルに合わせた敵が出現）")
    async def battle(self, interaction: discord.Interaction):
        await execute_battle(interaction, is_event=False)

    @app_commands.command(name="battle_event", description="【イベント】強力なガチャキャラボスに挑みます！")
    async def battle_event(self, interaction: discord.Interaction):
        await execute_battle(interaction, is_event=True)


async def setup(bot):
    await bot.add_cog(BattleCog(bot))
