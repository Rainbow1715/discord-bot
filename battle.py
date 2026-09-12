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
    "target_gacha_name": "ロイ",
    "boss_level": 100,
    "hp_multiplier": 5.0,
    "atk_multiplier": 1.2,
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
        
        # 👫 性別（未設定の場合は "不明"）
        self.gender = data_dict.get("gender", "不明")
        
        # ⚔️ 攻撃タイプ（物理 / 魔法）
        self.atk_type = data_dict.get("atk_type", "物理")
        
        self.level = data_dict.get("level", 1)
        self.max_hp = data_dict.get("hp", 100)
        self.hp = self.max_hp
        self.atk = data_dict.get("atk", 15)
        self.spd = data_dict.get("spd", 10)
        self.rec = data_dict.get("rec", 0)
        
        # スキル関連パラメータ
        self.skill_name = data_dict.get("skill_name", "通常攻撃")
        self.skill_pow = data_dict.get("skill_pow", 20)
        self.skill_type = data_dict.get("skill_type", "normal")
        
        # 💖 魅了の対象（"女", "男", "ALL" など。未設定なら "ALL"）
        self.charm_target = data_dict.get("charm_target", "ALL")
        
        # ⏱️ キャラ個別の発動タイミング & 発動率設定
        self.skill_trigger = data_dict.get("skill_trigger", "chance")
        self.skill_rate = data_dict.get("skill_rate", 35)

        self.is_boss = is_boss

    def should_use_skill(self, current_turn):
        """キャラ設定に基づいてスキルを発動するかどうか判定する"""
        trigger = self.skill_trigger
        
        if trigger == "always":
            return True
        elif trigger == "first_turn":
            if current_turn == 1:
                return random.randint(1, 100) <= self.skill_rate
            return False
        elif trigger == "hp_below_50":
            if (self.hp / self.max_hp) <= 0.5:
                return random.randint(1, 100) <= self.skill_rate
            return False
        elif trigger == "interval_3":
            if current_turn % 3 == 0:
                return random.randint(1, 100) <= self.skill_rate
            return False
        else:
            return random.randint(1, 100) <= self.skill_rate

    def action(self, target, party, current_turn, target_state):
        type_icon = "⚔️" if self.atk_type == "物理" else "🔮"

        # スキル発動判定
        if self.should_use_skill(current_turn):
            # ① 全体回復スキル
            if self.skill_type == "heal_all":
                healed_names = []
                for p in party:
                    if p.hp > 0:
                        p.hp = min(p.max_hp, p.hp + int(p.max_hp * 0.5))
                        healed_names.append(p.name)
                if healed_names:
                    return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{', '.join(healed_names)}** のHPが回復した！"
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ しかし効果がなかった！"

            # ② 物理特化ダメージ
            elif self.skill_type == "physical":
                dmg = self.skill_pow + int(self.atk * 0.5)
                target.hp = max(0, target.hp - dmg)
                return f"💥 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** に **{dmg}** ダメージ！"

            # ③ スタン（2ターン行動不能）
            elif self.skill_type == "stun":
                target_state["stun"] = 2
                return f"🌀 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** は動揺して **2ターン行動不能** になった！"

            # ④ 💖 魅了（対象の性別判定を追加）
            elif self.skill_type == "charm":
                # 対象の性別が指定された標的と一致するか、または標的が"ALL"の場合のみ成功
                if self.charm_target == "ALL" or target.gender == self.charm_target:
                    target_state["charm"] = 3
                    return f"💖 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** は魅了されて **3ターン行動不能** になった！"
                else:
                    # 性別が合致しなかった場合は効かない
                    return f"💖 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ しかし **{target.name}** には効かなかった！"

            # ⑤ 通常の単体攻撃スキル
            else:
                dmg = self.skill_pow + self.atk + random.randint(-3, 3)
                target.hp = max(0, target.hp - dmg)
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** に **{dmg}** ダメージ！"
        else:
            # 通常攻撃
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
            "gender": candidate.get("gender", "？"), # 元キャラの性別を使用（未設定なら「？」）
            "atk_type": candidate.get("atk_type", random.choice(["物理", "魔法"])),
            "level": boss_lvl,
            "hp": calculated_hp,
            "atk": calculated_atk,
            "spd": candidate.get("spd", 10),
            "rec": candidate.get("rec", 0),
            "skill_name": candidate.get("skill_name", "極大攻撃"),
            "skill_pow": candidate.get("skill_pow", 50),
            "skill_type": candidate.get("skill_type", "normal"),
            "charm_target": candidate.get("charm_target", "ALL"),
            "skill_trigger": candidate.get("skill_trigger", "chance"),
            "skill_rate": candidate.get("skill_rate", 35),
        }
        title_name = EVENT_CONFIG["name"]
        rewards = (EVENT_CONFIG["reward_gold"], EVENT_CONFIG["reward_rainbow"], EVENT_CONFIG["reward_exp"])
    else:
        boss_lvl = max(1, avg_level)
        boss_data = {
            "name": f"【Lv.{boss_lvl}】野生のモンスター",
            "icon": "👹",
            "element": "無",
            "gender": "？",
            "atk_type": random.choice(["物理", "魔法"]),
            "level": boss_lvl,
            "hp": 80 + (boss_lvl * 25),
            "atk": 10 + (boss_lvl * 4),
            "spd": 10,
            "rec": 0,
            "skill_name": "なぎ払い",
            "skill_pow": 15 + (boss_lvl * 2),
            "skill_type": "normal",
            "skill_trigger": "chance",
            "skill_rate": 35
        }
        title_name = "通常クエスト"
        rewards = ((1000, 3000), (50, 100), (50, 100))

    boss = Character(boss_data, is_boss=True)

    party_desc = ', '.join([f"**{p.name}** [{p.atk_type}] (Lv.{p.level})" for p in party])

    embed = discord.Embed(
        title=f"⚔️ {title_name} 開始！",
        description=f"立ちはだかる敵: **{boss.name}** ({boss.gender}) [{boss.atk_type}]\n出撃メンバー: {party_desc}",
        color=0xE74C3C if is_event else 0x3498DB,
    )
    await interaction.response.send_message(embed=embed)
    battle_msg = await interaction.original_response()

    turn = 1
    logs = []
    
    states = {boss: {"stun": 0, "charm": 0}}
    for p in party:
        states[p] = {"stun": 0, "charm": 0}

    while boss.hp > 0 and any(p.hp > 0 for p in party):
        await asyncio.sleep(1.8)
        turn_log = f"**--- ターン {turn} ---**\n"

        # 1. 味方のターン
        for p in party:
            if p.hp > 0 and boss.hp > 0:
                p_state = states[p]

                if p_state["stun"] > 0:
                    turn_log += f"💫 **{p.name}** は動けない！（残り {p_state['stun']} ターン）\n"
                    p_state["stun"] -= 1

                elif p_state["charm"] > 0:
                    turn_log += f"💖 **{p.name}** は魅了されてうっとりしている！（残り {p_state['charm']} ターン）\n"
                    p_state["charm"] -= 1

                else:
                    turn_log += p.action(boss, party, turn, states[boss]) + "\n"

        # 2. ボスのターン
        if boss.hp > 0:
            boss_state = states[boss]

            if boss_state["stun"] > 0:
                turn_log += f"💫 **{boss.name}** は動けない！（残り {boss_state['stun']} ターン）\n"
                boss_state["stun"] -= 1

            elif boss_state["charm"] > 0:
                turn_log += f"💖 **{boss.name}** は魅了されてうっとりしている！（残り {boss_state['charm']} ターン）\n"
                boss_state["charm"] -= 1

            else:
                alive_party = [p for p in party if p.hp > 0]
                if alive_party:
                    target = random.choice(alive_party)
                    turn_log += boss.action(target, [boss], turn, states[target]) + "\n"

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

    await asyncio.sleep(1.0)
    if boss.hp <= 0:
        (g_min, g_max), (r_min, r_max), (e_min, e_max) = rewards
        gold_gained = random.randint(g_min, g_max)
        rainbow_gained = random.randint(r_min, r_max)
        exp_gained = random.randint(e_min, e_max)

        u_data["gold"] = u_data.get("gold", 0) + gold_gained
        u_data["items"]["虹の欠片"] = u_data["items"].get("虹の欠片", 0) + rainbow_gained

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
        await on_battle_lose(interaction, u_data)
        save_data()

        result_embed = discord.Embed(
            title="💀 GAME OVER...",
            description="全滅してしまった...",
            color=0xFF0000,
        )

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
