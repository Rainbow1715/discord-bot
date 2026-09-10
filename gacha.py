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

# --------------------------------------------------
# ⚙️ ピックアップ率の設定（database.py側に定義があればそちらを優先）
# --------------------------------------------------
try:
    from database import NEW_PICKUP_BOOST_RATE, BIRTHDAY_PICKUP_BOOST_RATE
except ImportError:
    # database.py に個別の設定がない場合のデフォルト値（例: 新キャラ30% / バースデー30%）
    NEW_PICKUP_BOOST_RATE = 0.30
    BIRTHDAY_PICKUP_BOOST_RATE = 0.30


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
    # 当該レア度プール内に存在するピックアップ対象を抽出
    new_pickups_in_pool = [c for c in pool if c.get("name") in NEW_PICKUP_CHARACTERS]
    birthday_pickups_in_pool = [c for c in pool if c.get("name") in PICKUP_CHARACTERS]

    rand_val = random.random()

    # 🆕 A) 新実装ピックアップ判定
    if new_pickups_in_pool and rand_val < NEW_PICKUP_BOOST_RATE:
        return random.choice(new_pickups_in_pool)

    # 🎂 B) バースデーピックアップ判定
    # （新キャラ判定に漏れた後、次の確率帯でチェック）
    if birthday_pickups_in_pool and rand_val < (NEW_PICKUP_BOOST_RATE + BIRTHDAY_PICKUP_BOOST_RATE):
        return random.choice(birthday_pickups_in_pool)

    # 5. 通常選出（すり抜け）
    return random.choice(pool)


def draw_10_gacha():
    """10連ガチャを引く処理"""
    results = []
    for _ in range(10):
        results.append(select_character_by_rarity())
    return results


class GachaView(discord.ui.View):
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
            
            # 🎯 ピックアップマークの作成（新実装 🆕 / バースデー 🎂）
            pickup_marks = ""
            if char_name in NEW_PICKUP_CHARACTERS:
                pickup_marks += "🆕"
            if char_name in PICKUP_CHARACTERS:
                pickup_marks += "🎂"
            if pickup_marks:
                pickup_marks += " "

            # キャラ固有のiconが設定されていればそれを優先
            char_icon = template.get("icon")
            if char_icon:
                rarity_icon = char_icon
            else:
                rarity_icon = "✨" if template.get("rarity") == "★5" else ("🌟" if template.get("rarity") == "★4" else "")

            existing_char = next((c for c in user_chars if c["name"] == template["name"]), None)

            if existing_char:
                existing_char["count"] = existing_char.get("count", 1) + 1
                # 重複時のステータス上昇処理
                existing_char["max_hp"] = existing_char.get("max_hp", existing_char.get("hp", 100)) + 2
                existing_char["hp"] = existing_char.get("hp", 100) + 2
                existing_char["atk"] = existing_char.get("atk", 10) + 1
                status_note = f"[重複 +1] (所持数: {existing_char['count']})"
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

        # --------------------------------------------------
        # 🎰 ガチャ実行回数の加算 ＆ 実績チェック
        # --------------------------------------------------
        u_data["gacha_count"] = u_data.get("gacha_count", 0) + 1
        obtained_names = [t.get("name") for t in drawn_templates if t and t.get("name")]
        
        save_data()

        await on_gacha_draw(interaction, u_data)
        await check_character_achievements(interaction, u_data, obtained_names)

        embed = discord.Embed(
            title="🎰 10連ガチャ結果！",
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
