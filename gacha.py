import random
import discord
# database から必要な定数・関数を読み込み
from database import (
    GACHA_POOL, 
    RARITY_RATES, 
    PICKUP_CHARACTERS,       # 🎂 バースデーピックアップ
    NEW_PICKUP_CHARACTERS,   # 🆕 新実装ピックアップ
    PICKUP_BOOST_RATE,       # フォールバック用
    get_user_profile, 
    save_data
)
from achievement import on_gacha_draw, check_character_achievements
from cogs.soubi import EQUIPMENT_MASTER

# --------------------------------------------------
# ⚙️ ピックアップ率の設定（database.py側に定義があればそちらを優先）
# --------------------------------------------------
try:
    from database import NEW_PICKUP_BOOST_RATE, BIRTHDAY_PICKUP_BOOST_RATE
except ImportError:
    # database.py に個別の設定がない場合のデフォルト値（例: 新キャラ30% / バースデー30%）
    NEW_PICKUP_BOOST_RATE = 0.30
    BIRTHDAY_PICKUP_BOOST_RATE = 0.30


# ==================================================
# 👤 キャラガチャ用処理
# ==================================================

def select_character_by_rarity():
    """レア度確率に基づいてキャラを1体抽選する（ピックアップ枠を分離）"""
    # 1. 重み付きランダムでレア度を決定
    rarities = list(RARITY_RATES.keys())
    weights = list(RARITY_RATES.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    
    # 2. 選ばれたレア度のキャラリストを取得
    pool = [c for c in GACHA_POOL if c.get("rarity") == chosen_rarity]

    # 3. 該当レア度のキャラが未実装の場合のフォールバック処理
    if not pool:
        non_star5_pool = [c for c in GACHA_POOL if c.get("rarity") != "★5"]
        if non_star5_pool:
            pool = non_star5_pool
        else:
            pool = GACHA_POOL

    if not pool:
        return GACHA_POOL[0] if GACHA_POOL else None

    # --------------------------------------------------
    # 4. 🎯 ピックアップ判定（枠を分離）
    # --------------------------------------------------
    new_pickups_in_pool = [c for c in pool if c.get("name") in NEW_PICKUP_CHARACTERS]
    birthday_pickups_in_pool = [c for c in pool if c.get("name") in PICKUP_CHARACTERS]

    rand_val = random.random()

    # 🆕 A) 新実装ピックアップ判定
    if new_pickups_in_pool and rand_val < NEW_PICKUP_BOOST_RATE:
        return random.choice(new_pickups_in_pool)

    # 🎂 B) バースデーピックアップ判定
    if birthday_pickups_in_pool and rand_val < (NEW_PICKUP_BOOST_RATE + BIRTHDAY_PICKUP_BOOST_RATE):
        return random.choice(birthday_pickups_in_pool)

    # 5. 通常選出（すり抜け）
    return random.choice(pool)


def draw_10_gacha():
    """10連キャラガチャを引く処理"""
    results = []
    for _ in range(10):
        results.append(select_character_by_rarity())
    return results


class GachaView(discord.ui.View):
    """キャラガチャ用 View"""
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def process_gacha(self, interaction: discord.Interaction, cost_type: str):
        # 1. ユーザーチェック
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーのガチャ画面です。", ephemeral=True)
            return

        # 2. 「考え中…」にしてタイムアウトを延ばす
        await interaction.response.defer()

        u_data = get_user_profile(self.user_id)
        items = u_data["items"]

        # コストチェックと消費
        if cost_type == "rainbow":
            if items.get("虹の欠片", 0) < 1000:
                await interaction.followup.send("❌ 虹の欠片が足りません！（必要: 1000個）", ephemeral=True)
                return
            items["虹の欠片"] -= 1000
        elif cost_type == "ticket":
            if items.get("ガチャチケ", 0) < 10:
                await interaction.followup.send("❌ ガチャチケが足りません！（必要: 10枚）", ephemeral=True)
                return
            items["ガチャチケ"] -= 10

        # ガチャの実行
        drawn_templates = draw_10_gacha()
        user_chars = u_data["characters"]
        result_lines = []

        for idx, template in enumerate(drawn_templates, start=1):
            if not template:
                continue

            char_name = template.get("name", "")
            
            # 🎯 ピックアップマークの作成
            pickup_marks = ""
            if char_name in NEW_PICKUP_CHARACTERS:
                pickup_marks += "🆕"
            if char_name in PICKUP_CHARACTERS:
                pickup_marks += "🎂"
            if pickup_marks:
                pickup_marks += " "

            # アイコン指定
            char_icon = template.get("icon")
            if char_icon:
                rarity_icon = char_icon
            else:
                rarity_icon = "✨" if template.get("rarity") == "★5" else ("🌟" if template.get("rarity") == "★4" else "")

            existing_char = next((c for c in user_chars if c["name"] == template["name"]), None)

            if existing_char:
                existing_char["count"] = existing_char.get("count", 1) + 1
                status_note = f"[所持数: {existing_char['count']}]"
            else:
                new_char = {
                    "name": template["name"],
                    "rarity": template.get("rarity", "★3"),
                    "icon": template.get("icon"),
                    "count": 1,
                    "level": 1,
                    "exp": 0,
                    "max_hp": template.get("max_hp", template.get("hp", 100)),
                    "hp": template.get("hp", 100),
                    "atk": template.get("atk", 10),
                    "spd": template.get("spd", 10),
                    "rec": template.get("rec", 10),
                    "skill_name": template.get("skill_name", "通常攻撃"),
                    "skill_pow": template.get("skill_pow", 1.0),
                }
                user_chars.append(new_char)
                status_note = "**[✨NEW!✨]**"

            # 表示テキストの作成
            result_lines.append(f"{idx}. {pickup_marks}{rarity_icon} **[{template.get('rarity', '★3')}] {char_name}** {status_note}")

        # 🎰 ガチャ実行回数の加算 ＆ 実績チェック
        u_data["gacha_count"] = u_data.get("gacha_count", 0) + 1
        obtained_names = [t.get("name") for t in drawn_templates if t and t.get("name")]
        
        save_data()

        await on_gacha_draw(interaction, u_data)
        await check_character_achievements(interaction, u_data, obtained_names)

        embed = discord.Embed(
            title="🎰 10連キャラガチャ結果！",
            description="\n".join(result_lines),
            color=0xFFD700
        )
        embed.set_footer(
            text=f"残高 ｜ 虹の欠片: {items.get('虹の欠片', 0)}個 / ガチャチケ: {items.get('ガチャチケ', 0)}枚"
        )

        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="虹の欠片 1000個で10連", style=discord.ButtonStyle.primary, emoji="💎")
    async def draw_rainbow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "rainbow")

    @discord.ui.button(label="ガチャチケ 10枚で10連", style=discord.ButtonStyle.success, emoji="🎫")
    async def draw_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "ticket")


# ==================================================
# 🗡️ 装備ガチャ用処理（※単発なし・10連のみ）
# ==================================================

def draw_10_equipment_gacha():
    """EQUIPMENT_MASTER から直接10連分抽選し、ユーザー保存用のデータ形式で返す"""
    if not EQUIPMENT_MASTER:
        return []

    equip_names = list(EQUIPMENT_MASTER.keys())
    weights = []

    # レアリティに応じた確率の重み付け（★5:5%, ★4:25%, ★3:70%）
    for name in equip_names:
        data = EQUIPMENT_MASTER[name]
        rarity = data.get("rarity", 3)
        if rarity == 5 or rarity == "★5":
            weights.append(5)
        elif rarity == 4 or rarity == "★4":
            weights.append(25)
        else:
            weights.append(70)

    # 重み付きランダムで装備名を10個選択
    chosen_names = random.choices(equip_names, weights=weights, k=10)

    # 所持データ・表示用に辞書オブジェクト化
    drawn_items = []
    for name in chosen_names:
        master_info = EQUIPMENT_MASTER[name].copy()
        master_info["name"] = name
        drawn_items.append(master_info)

    return drawn_items


class SoubiGachaView(discord.ui.View):
    """装備ガチャ用 View（10連のみ）"""
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def process_gacha(self, interaction: discord.Interaction, cost_type: str):
        # 1. ユーザーチェック
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーのガチャ画面です。", ephemeral=True)
            return

        # 2. 応答の保留
        await interaction.response.defer()

        u_data = get_user_profile(self.user_id)
        items = u_data.setdefault("items", {})

        # 3. コストチェックと消費
        if cost_type == "rainbow":
            if items.get("虹の欠片", 0) < 1000:
                await interaction.followup.send("❌ 虹の欠片が足りません！（必要: 1000個）", ephemeral=True)
                return
            items["虹の欠片"] -= 1000
            
        elif cost_type == "ticket":
            if items.get("装備ガチャチケット", 0) < 10:
                await interaction.followup.send(
                    f"❌ 装備ガチャチケットが足りません！（所持: {items.get('装備ガチャチケット', 0)}枚 / 必要: 10枚）", 
                    ephemeral=True
                )
                return
            items["装備ガチャチケット"] -= 10

        # 4. 装備10連の実行
        drawn_equipments = draw_10_equipment_gacha()
        user_equipments = u_data.setdefault("equipments", [])

        result_lines = []
        has_ur = False

        for idx, equip in enumerate(drawn_equipments, start=1):
            name = equip.get("name", "謎の装備")
            rarity = equip.get("rarity", 3)
            icon = equip.get("icon", "⚔️")

            # レア度別のテキスト表示調整
            if rarity == 5 or rarity == "★5":
                rarity_str = "⭐⭐⭐⭐⭐"
                rarity_tag = "✨**UR**✨"
                has_ur = True
            elif rarity == 4 or rarity == "★4":
                rarity_str = "⭐⭐⭐⭐"
                rarity_tag = "🌟SR"
            else:
                rarity_str = "⭐⭐⭐"
                rarity_tag = "R"

            # ユーザーの所持装備リストに追加
            user_equipments.append({
                "name": name,
                "rarity": rarity,
                "icon": icon,
                "atk": equip.get("atk", 0),
                "description": equip.get("description", ""),
                # 必要に応じて level: 1 や exp: 0 などを初期化
            })

            result_lines.append(f"`{idx:2d}.` {icon} **[{rarity_str}] {name}** ({rarity_tag})")

        # 5. ガチャカウント加算・データ保存・実績呼び出し
        u_data["gacha_count"] = u_data.get("gacha_count", 0) + 1
        save_data()

        await on_gacha_draw(interaction, u_data)

        # 6. Embed表示
        embed = discord.Embed(
            title="🗡️ 10連装備ガチャ結果！",
            description="\n".join(result_lines),
            color=0xFFD700 if has_ur else 0x3498DB
        )
        embed.set_footer(
            text=f"残高 ｜ 虹の欠片: {items.get('虹の欠片', 0)}個 / 装備ガチャチケット: {items.get('装備ガチャチケット', 0)}枚"
        )

        await interaction.edit_original_response(embed=embed, view=None)

    # 💎 虹の欠片ボタン
    @discord.ui.button(label="虹の欠片 1000個で10連", style=discord.ButtonStyle.primary, emoji="💎")
    async def draw_rainbow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "rainbow")

    # 🎟️ 装備ガチャチケットボタン
    @discord.ui.button(label="装備ガチャチケ 10枚で10連", style=discord.ButtonStyle.success, emoji="🎟️")
    async def draw_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "ticket")
