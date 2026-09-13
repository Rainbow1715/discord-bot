import asyncio
import random
import discord
from discord import app_commands
from discord.ext import commands
from database import get_user_profile, save_data, GACHA_POOL
from achievement import on_battle_win, on_battle_lose

EVENT_CONFIG = {
    "name": "【特別イベント】vsカス",
    # ── 👤 1体モード（単体ボス）の設定 ──
    "single_mode": {
        "title": "【単体】vsカス",
        "candidates": ["ロイ", "折原和也", "神明龍矢"],
        "boss_level": 80,
        "hp_multiplier": 3.0,
        "atk_multiplier": 1.0,
        "reward_gold": (5000, 8000),
        "reward_rainbow": (2000, 3000),
        "reward_exp": (2000, 3000),
    },
    # ── 👹 複数体モード（ラッシュボス）の設定 ──
    "multi_mode": {
        "title": "【狂乱】カス三人衆を連れてきたよ。",
        "candidates": ["ロイ", "折原和也", "神明龍矢"],
        "max_spawn": 3,
        "boss_level": 100,
        "hp_multiplier": 2.5,
        "atk_multiplier": 1.1,
        "reward_gold": (8000, 15000),
        "reward_rainbow": (3000, 6000),
        "reward_exp": (3000, 5000),
    }
}


def create_smooth_bar(ratio: float, length: int = 10) -> str:
    ratio = max(0.0, min(1.0, ratio))
    filled_length = int(length * ratio)
    if ratio > 0 and filled_length == 0:
        filled_length = 1
    filled_bar = "█" * filled_length
    empty_bar = "⬜︎" * (length - filled_length)
    return filled_bar + empty_bar


class Character:
    def __init__(self, data_dict: dict, is_boss: bool = False):
        self.data = data_dict
        self.name = data_dict.get("name", "謎の敵")
        self.icon = data_dict.get("icon", "👤")
        self.element = data_dict.get("element", "無")
        self.gender = data_dict.get("gender", "不明")
        self.atk_type = data_dict.get("atk_type", "物理")
        
        self.level = data_dict.get("level", 1)
        self.max_hp = data_dict.get("max_hp", data_dict.get("hp", 100))
        self.hp = self.max_hp
        self.atk = data_dict.get("atk", 15)
        self.spd = data_dict.get("spd", 10)
        self.rec = data_dict.get("rec", 0)
        
        self.skill_name = data_dict.get("skill_name", "通常攻撃")
        self.skill_pow = data_dict.get("skill_pow", 1.0)
        self.skill_type = data_dict.get("skill_type", "normal")
        self.charm_target = data_dict.get("charm_target", "ALL")
        self.skill_trigger = data_dict.get("skill_trigger", "chance")
        self.skill_rate = data_dict.get("skill_rate", 35)

        self.is_boss = is_boss
        self.buffs = []

    def get_effective_atk(self) -> int:
        atk_multiplier = 1.0
        for buff in self.buffs:
            if buff.get("type") == "atk_up":
                atk_multiplier += buff.get("value", 0.0)
        return int(self.atk * atk_multiplier)

    def should_use_skill(self, current_turn: int) -> bool:
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

    def action(self, target, party, current_turn: int, target_state: dict) -> str:
        type_icon = "⚔️" if self.atk_type == "物理" else "🔮"
        current_atk = self.get_effective_atk()

        if self.should_use_skill(current_turn):
            if self.skill_type == "heal_all":
                healed_names = []
                for p in party:
                    if p.hp > 0:
                        p.hp = min(p.max_hp, p.hp + int(p.max_hp * 0.5))
                        healed_names.append(p.name)
                if healed_names:
                    return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{', '.join(healed_names)}** のHPが回復した！"
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ しかし効果がなかった！"

            elif self.skill_type == "buff_all_atk":
                boost_rate = float(self.skill_pow) if isinstance(self.skill_pow, (int, float)) else 0.20
                buff_target_party = party if not self.is_boss else [self]
                buffed_names = []
                for member in buff_target_party:
                    if member.hp > 0:
                        member.buffs.append({"type": "atk_up", "value": boost_rate, "duration": 3})
                        buffed_names.append(member.name)
                percent = int(boost_rate * 100)
                return f"🔥 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{', '.join(buffed_names)}** の攻撃力が3ターンの間 **{percent}%** アップ！"

            elif self.skill_type == "physical":
                dmg = int(self.skill_pow + (current_atk * 0.5))
                dmg = max(1, dmg)
                target.hp = max(0, target.hp - dmg)
                return f"💥 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** に **{dmg}** ダメージ！"

            elif self.skill_type == "stun":
                target_state["stun"] = 2
                return f"🌀 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** は動揺して **2ターン行動不能** になった！"

            elif self.skill_type == "charm":
                if self.charm_target == "ALL" or target.gender == self.charm_target:
                    target_state["charm"] = 3
                    return f"💖 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** は魅了されて **3ターン行動不能** になった！"
                else:
                    return f"💖 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ しかし **{target.name}** には効かなかった！"

            else:
                pow_val = float(self.skill_pow) if isinstance(self.skill_pow, (int, float)) else 15.0
                dmg = int(pow_val + current_atk + random.randint(-3, 3))
                dmg = max(1, dmg)
                target.hp = max(0, target.hp - dmg)
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{target.name}** に **{dmg}** ダメージ！"
        else:
            dmg = max(1, current_atk + random.randint(-2, 2))
            target.hp = max(0, target.hp - dmg)
            return f"{type_icon} {self.icon} **{self.name}** の{self.atk_type}攻撃！ **{target.name}** に **{dmg}** ダメージ！"


class EventModeSelectView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のプレイヤーの選択パネルです。", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👤 1体モード（ランダム1体）", style=discord.ButtonStyle.primary, custom_id="mode_single")
    async def select_single(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.defer()
        await execute_battle(interaction, is_event=True, event_mode="single", target_message=interaction.message)

    @discord.ui.button(label="👹 強敵ラッシュ（最大3体）", style=discord.ButtonStyle.danger, custom_id="mode_multi")
    async def select_multi(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.defer()
        await execute_battle(interaction, is_event=True, event_mode="multi", target_message=interaction.message)


async def execute_battle(interaction: discord.Interaction, is_event: bool = False, event_mode: str = "single", target_message: discord.Message = None):
    u_data = get_user_profile(interaction.user.id)
    party = [Character(u_data["characters"][i]) for i in u_data["party_indices"] if i < len(u_data["characters"])]

    if not party:
        msg = "❌ パーティメンバーがセットされていません。`/party` で編成してください！"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    avg_level = sum(p.level for p in party) // len(party)
    enemies = []
    
    # 👹 敵の生成分岐
    if is_event:
        mode_config = EVENT_CONFIG.get(f"{event_mode}_mode", EVENT_CONFIG.get("single_mode"))
        target_names = mode_config.get("candidates", [])

        boss_candidates = [c for c in GACHA_POOL if c["name"] in target_names]
        if not boss_candidates:
            boss_candidates = GACHA_POOL.copy()

        if event_mode == "single":
            spawn_count = 1
        else:
            max_spawn = mode_config.get("max_spawn", 3)
            spawn_count = min(len(boss_candidates), max_spawn)

        selected_candidates = random.sample(boss_candidates, k=spawn_count)
        boss_lvl = mode_config.get("boss_level", 100)

        for i, candidate in enumerate(selected_candidates):
            calculated_hp = int((candidate.get("max_hp", candidate.get("hp", 100)) + (boss_lvl * 15)) * mode_config.get("hp_multiplier", 3.0))
            calculated_atk = int((candidate.get("atk", 15) + (boss_lvl * 3)) * mode_config.get("atk_multiplier", 1.0))

            boss_name_suffix = f"{chr(65+i)}" if selected_candidates.count(candidate) > 1 else ""

            boss_data = {
                "name": f"【Lv.{boss_lvl}】{candidate['name']}{boss_name_suffix}",
                "icon": candidate.get("icon", "👹"),
                "element": candidate.get("element", "無"),
                "gender": candidate.get("gender", "？"),
                "atk_type": candidate.get("atk_type", random.choice(["物理", "魔法"])),
                "level": boss_lvl,
                "max_hp": calculated_hp,
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
            enemies.append(Character(boss_data, is_boss=True))

        title_name = mode_config.get("title", EVENT_CONFIG["name"])
        rewards = (mode_config["reward_gold"], mode_config["reward_rainbow"], mode_config["reward_exp"])
        enemy_multiplier = spawn_count

    else:
        if avg_level >= 40:
            enemy_count = 3
        elif avg_level >= 25:
            enemy_count = 2
        else:
            enemy_count = 1

        boss_lvl = max(1, avg_level)
        
        for i in range(enemy_count):
            enemy_name = "野生のモンスター" if enemy_count == 1 else f"野生のモンスター{chr(65+i)}"
            enemy_data = {
                "name": f"【Lv.{boss_lvl}】{enemy_name}",
                "icon": "👹",
                "element": "無",
                "gender": "？",
                "atk_type": random.choice(["物理", "魔法"]),
                "level": boss_lvl,
                "max_hp": 80 + (boss_lvl * 25),
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
            enemies.append(Character(enemy_data, is_boss=True))
            
        title_name = "通常クエスト"
        rewards = ((1000, 3000), (50, 100), (50, 100))
        enemy_multiplier = enemy_count

    enemy_desc = ", ".join([f"**{e.name}**" for e in enemies])
    party_desc = ', '.join([f"**{p.name}** [{p.atk_type}] (Lv.{p.level})" for p in party])

    start_embed = discord.Embed(
        title=f"⚔️ {title_name} 開始！",
        description=f"立ちはだかる敵: {enemy_desc}\n出撃メンバー: {party_desc}",
        color=0xE74C3C if is_event else 0x3498DB,
    )

    # ⭕️ メッセージの取得/送信用ハンドリング
    if target_message:
        battle_msg = target_message
        await battle_msg.edit(content=None, embed=start_embed, view=None)
    else:
        await interaction.response.send_message(embed=start_embed)
        battle_msg = await interaction.original_response()

    turn = 1
    logs = []
    states = {unit: {"stun": 0, "charm": 0} for unit in party + enemies}

    # ------------------ バトル進行ループ ------------------
    while any(e.hp > 0 for e in enemies) and any(p.hp > 0 for p in party):
        await asyncio.sleep(1.8)
        turn_log = f"**--- ターン {turn} ---**\n"

        # 1. 味方のターン
        for p in party:
            if p.hp > 0 and any(e.hp > 0 for e in enemies):
                p_state = states[p]

                if p_state["stun"] > 0:
                    turn_log += f"💫 **{p.name}** は動けない！（残り {p_state['stun']} ターン）\n"
                    p_state["stun"] -= 1

                elif p_state["charm"] > 0:
                    turn_log += f"💖 **{p.name}** は魅了されてうっとりしている！（残り {p_state['charm']} ターン）\n"
                    p_state["charm"] -= 1

                else:
                    alive_enemies = [e for e in enemies if e.hp > 0]
                    target_enemy = random.choice(alive_enemies)
                    turn_log += p.action(target_enemy, party, turn, states[target_enemy]) + "\n"

        # 2. 敵のターン
        for enemy in enemies:
            if enemy.hp > 0 and any(p.hp > 0 for p in party):
                enemy_state = states[enemy]

                if enemy_state["stun"] > 0:
                    turn_log += f"💫 **{enemy.name}** は動けない！（残り {enemy_state['stun']} ターン）\n"
                    enemy_state["stun"] -= 1

                elif enemy_state["charm"] > 0:
                    turn_log += f"💖 **{enemy.name}** は魅了されてうっとりしている！（残り {enemy_state['charm']} ターン）\n"
                    enemy_state["charm"] -= 1

                else:
                    alive_party = [p for p in party if p.hp > 0]
                    if alive_party:
                        target_player = random.choice(alive_party)
                        turn_log += enemy.action(target_player, enemies, turn, states[target_player]) + "\n"

        # バフ減衰処理
        all_units = party + enemies
        for unit in all_units:
            active_buffs = []
            for buff in unit.buffs:
                buff["duration"] -= 1
                if buff["duration"] > 0:
                    active_buffs.append(buff)
                else:
                    turn_log += f"⌛ **{unit.name}** の攻撃力アップ効果が切れた。\n"
            unit.buffs = active_buffs
        
        logs.append(turn_log)
        if len(logs) > 2:
            logs.pop(0)

        status_text = "\n"
        for enemy in enemies:
            enemy_bar = create_smooth_bar(enemy.hp / enemy.max_hp)
            status_text += f"{enemy.icon} **{enemy.name}**: HP {enemy.hp}/{enemy.max_hp} {enemy_bar}\n"

        status_text += "-------------------\n"

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
    
    # ------------------ 勝敗判定 ------------------
    if all(e.hp <= 0 for e in enemies):
        (g_min, g_max), (r_min, r_max), (e_min, e_max) = rewards
        gold_gained = random.randint(g_min, g_max) * enemy_multiplier
        rainbow_gained = random.randint(r_min, r_max) * enemy_multiplier
        exp_gained = random.randint(e_min, e_max) * enemy_multiplier

        u_data["gold"] = u_data.get("gold", 0) + gold_gained
        user_items = u_data.setdefault("items", {})
        user_items["虹の欠片"] = user_items.get("虹の欠片", 0) + rainbow_gained

        await on_battle_win(interaction, u_data)

        MAX_LEVEL = 99
        lvl_up_msgs = []
        for p in party:
            c_data = p.data

            if c_data.get("level", 1) >= MAX_LEVEL:
                continue

            c_data["exp"] = c_data.get("exp", 0) + exp_gained
            leveled_up = False

            for _ in range(100):
                if c_data.get("level", 1) >= MAX_LEVEL:
                    c_data["exp"] = 0
                    break

                next_exp = c_data.get("level", 1) * 100
                if c_data["exp"] >= next_exp:
                    c_data["exp"] -= next_exp
                    c_data["level"] = c_data.get("level", 1) + 1
                    c_data["max_hp"] = c_data.get("max_hp", c_data.get("hp", 100)) + 8
                    c_data["hp"] = c_data["max_hp"]
                    c_data["atk"] = c_data.get("atk", 15) + 3
                    leveled_up = True
                else:
                    break

            if leveled_up:
                lvl_up_msgs.append(f"🎉 **{c_data['name']}** (Lv.{c_data['level']} にUP!)")

        save_data()
        lvl_str = "\n" + "\n".join(lvl_up_msgs) if lvl_up_msgs else ""
        bonus_str = f" (敵{enemy_multiplier}体討伐ボーナス!)" if enemy_multiplier > 1 else ""

        result_embed = discord.Embed(
            title="🎉 VICTORY!",
            description=(
                f"敵を全滅させた！{bonus_str}\n\n"
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
        
    await asyncio.sleep(0.5)
    await interaction.channel.send(embed=result_embed)


class BattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="battle", description="通常のクエストバトルを行います（味方のレベルに合わせた敵が出現）")
    async def battle(self, interaction: discord.Interaction):
        await execute_battle(interaction, is_event=False)

    @app_commands.command(name="battle_event", description="【特別イベント】強力な敵に挑みます！")
    async def event_battle_cmd(self, interaction: discord.Interaction):
        view = EventModeSelectView(user_id=interaction.user.id)
        embed = discord.Embed(
            title=f"🎪 {EVENT_CONFIG['name']}",
            description="挑む難易度（モード）を選択してください！",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(BattleCog(bot))
