import asyncio
import random
import discord
from database import get_user_profile, save_data

import discord
import random

# 属性相性表（攻撃側 -> 防御側: 倍率）
ELEMENT_EFFECTIVENESS = {
    "赤": {"緑": 1.5, "青": 0.8},
    "緑": {"青": 1.5, "赤": 0.8},
    "青": {"赤": 1.5, "緑": 0.8},
    "光": {"紫": 1.5},
    "紫": {"光": 1.5},
}

def get_effective_atk(char):
    """ベスト装備ならATK+20%補正"""
    base_atk = char["atk"]
    if char.get("equip") and char.get("equip") == char.get("best_equip"):
        return int(base_atk * 1.2)
    return base_atk

def get_element_multiplier(atk_elem, def_elem):
    """属性相性倍率を取得"""
    if not atk_elem or not def_elem:
        return 1.0
    return ELEMENT_EFFECTIVENESS.get(atk_elem, {}).get(def_elem, 1.0)

async def run_battle(interaction: discord.Interaction):
    # バトル処理の呼び出し例
    await interaction.response.send_message("⚔️ バトルを開始します！（仮実装）", ephemeral=True)

def create_smooth_bar(ratio, length=10):
    filled_length = int(length * ratio)
    if ratio > 0 and filled_length == 0:
        filled_length = 1

    filled_bar = "█" * filled_length
    empty_bar = "⬜︎" * (length - filled_length)
    return filled_bar + empty_bar

class Character:
    def __init__(self, data_dict):
        self.data = data_dict
        self.name = data_dict["name"]
        self.icon = data_dict.get("icon", "👤")
        self.max_hp = data_dict["hp"]
        self.hp = data_dict["hp"]
        self.atk = data_dict["atk"]
        self.spd = data_dict["spd"]
        self.rec = data_dict["rec"]
        self.skill_name = data_dict["skill_name"]
        self.skill_pow = data_dict["skill_pow"]
        self.skill_type = data_dict.get("skill_type", "normal")

    def action(self, target, party, boss_state):
        if random.randint(1, 100) <= 35:
            # 茉鈴：自分以外の味方全員をフル回復
            if self.skill_type == "heal_all":
                healed_names = []
                for p in party:
                    if p != self and p.hp > 0:
                        p.hp = p.max_hp
                        healed_names.append(p.name)

                if healed_names:
                    return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ **{', '.join(healed_names)}** のHPが全回復した！"
                else:
                    return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ しかし回復する対象がいない！"

            # 橘柊人：固定物理30ダメージ
            elif self.skill_type == "physical":
                dmg = self.skill_pow
                target.hp = max(0, target.hp - dmg)
                return f"💥 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ 敵に **{dmg}** の物理ダメージ！"

            # 河野蜜柑：敵を3ターン行動不能にする
            elif self.skill_type == "stun":
                boss_state["stun_turns"] = 3
                return f"🌀 {self.icon} **{self.name}** のスキル【{self.skill_name}】！ 敵は動揺して **3ターン行動不能** になった！"

            # 通常スキル
            else:
                dmg = self.skill_pow + random.randint(-3, 3)
                target.hp = max(0, target.hp - dmg)
                return f"✨ {self.icon} **{self.name}** のスキル【{self.skill_name}】！ 敵に {dmg} ダメージ！"
        else:
            dmg = self.atk + random.randint(-2, 2)
            target.hp = max(0, target.hp - dmg)
            return f"🗡️ {self.icon} **{self.name}** の攻撃！ 敵に {dmg} ダメージ！"

async def run_battle(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    party = [Character(u_data["characters"][i]) for i in u_data["party_indices"] if i < len(u_data["characters"])]

    boss_hp = 120
    max_boss_hp = 120

    embed = discord.Embed(
        title="⚔️ バトル開始！",
        description=f"パーティ ({', '.join([p.name for p in party])}) が出撃します！",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed)
    battle_msg = await interaction.original_response()

    turn = 1
    logs = []
    boss_state = {"stun_turns": 0}

    while boss_hp > 0 and any(p.hp > 0 for p in party):
        await asyncio.sleep(1.8)
        turn_log = f"**--- ターン {turn} ---**\n"

        class DummyBoss:
            pass

        boss = DummyBoss()
        boss.hp = boss_hp

        # 味方の攻撃
        for p in party:
            if p.hp > 0 and boss.hp > 0:
                turn_log += p.action(boss, party, boss_state) + "\n"

        boss_hp = boss.hp

        # 敵の攻撃（行動不能判定）
        if boss_hp > 0:
            if boss_state["stun_turns"] > 0:
                turn_log += f"💫 **ボス** は動けない！（残り {boss_state['stun_turns']} ターン）\n"
                boss_state["stun_turns"] -= 1
            else:
                alive_party = [p for p in party if p.hp > 0]
                if alive_party:
                    target = random.choice(alive_party)
                    enemy_dmg = random.randint(8, 15)
                    target.hp = max(0, target.hp - enemy_dmg)
                    turn_log += f"👹 **ボス** の攻撃！ {target.icon} **{target.name}** に {enemy_dmg} ダメージ！\n"

        logs.append(turn_log)
        if len(logs) > 2:
            logs.pop(0)

        boss_bar = create_smooth_bar(max(0, boss_hp) / max_boss_hp)
        status_text = f"\n👹 **ボス HP**: {boss_hp}/{max_boss_hp} {boss_bar}\n"

        for p in party:
            p_bar = create_smooth_bar(max(0, p.hp) / p.max_hp)
            status_text += f"{p.icon} **{p.name}**: HP {p.hp}/{p.max_hp} {p_bar}\n"

        new_embed = discord.Embed(
            title=f"⚔️ バトル進行中... (ターン {turn})",
            description="\n".join(logs) + status_text,
            color=0xFF9900,
        )
        await battle_msg.edit(embed=new_embed)
        turn += 1

    await asyncio.sleep(1.0)
    if boss_hp <= 0:
        exp_gained = random.randint(30, 100)
        gold_gained = random.randint(1000, 5000)
        rainbow_gained = random.randint(90, 150)

        u_data["gold"] += gold_gained
        u_data["items"]["虹の欠片"] = u_data["items"].get("虹の欠片", 0) + rainbow_gained

        lvl_up_msgs = []
        for p in party:
            c_data = p.data
            c_data["exp"] += exp_gained
            next_exp = c_data["level"] * 100
            if c_data["exp"] >= next_exp:
                c_data["level"] += 1
                c_data["hp"] += 5
                c_data["atk"] += 2
                lvl_up_msgs.append(f"🎉 **{c_data['name']}** (Lv.{c_data['level']} にUP!)")

        save_data()
        lvl_str = "\n" + "\n".join(lvl_up_msgs) if lvl_up_msgs else ""

        result_embed = discord.Embed(
            title="🎉 VICTORY!",
            description=(
                f"ボスを撃破した！\n\n"
                f"💰 **獲得金**: {gold_gained} G\n"
                f"💎 **獲得虹の欠片**: {rainbow_gained} 個\n"
                f"✨ **獲得経験値**: 出撃メンバー全員に {exp_gained} EXP"
                f"{lvl_str}"
            ),
            color=0x00FF00,
        )
    else:
        result_embed = discord.Embed(
            title="💀 GAME OVER...",
            description="全滅してしまった...",
            color=0xFF0000,
        )

    await interaction.followup.send(embed=result_embed)
