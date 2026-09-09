import random
import discord
from database import GACHA_POOL, RARITY_RATES, PICKUP_CHARACTERS, PICKUP_BOOST_RATE, get_user_profile, save_data
from achievement import check_and_unlock_achievement  # 👈 実実績解除関数をインポート

def select_character_by_rarity():
    """レア度確率に基づいてキャラを1体抽選する（フォールバック時は低レア優先）"""
    # 1. 重み付きランダムでレア度を決定
    rarities = list(RARITY_RATES.keys())
    weights = list(RARITY_RATES.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    
    # 2. 選ばれたレア度のキャラリストを取得
    pool = [c for c in GACHA_POOL if c.get("rarity") == chosen_rarity]

    # 3. 該当レア度のキャラが未実装の場合のフォールバック処理
    if not pool:
        # ★5を除外した、現在存在する低レア度プール（★3〜★4）に安全に流す
        non_star5_pool = [c for c in GACHA_POOL if c.get("rarity") != "★5"]
        if non_star5_pool:
            pool = non_star5_pool
        else:
            pool = GACHA_POOL

    # それでも万が一プール全体が空なら None を返す
    if not pool:
        return GACHA_POOL[0] if GACHA_POOL else None

    # 4. 🎂 ピックアップ判定
    # そのプール（選ばれたレア度）の中にピックアップ対象キャラが含まれているか確認
    pickup_in_pool = [c for c in pool if c.get("name") in PICKUP_CHARACTERS]
    if pickup_in_pool:
        # 指定した確率（90%など）でピックアップキャラを優先選出
        if random.random() < PICKUP_BOOST_RATE:
            return random.choice(pickup_in_pool)

    # 5. 通常選出
    return random.choice(pool)

def draw_10_gacha():
    """10連ガチャを引く処理"""
    results = []
    
    # 通常枠 10連
    for _ in range(10):
        results.append(select_character_by_rarity())

    return results


class GachaView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def process_gacha(self, interaction: discord.Interaction, cost_type: str):
        # 1. ユーザーチェック（他の人のガチャボタンを押した場合はここで弾く）
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーのガチャ画面です。", ephemeral=True)
            return

        # 2. 「考え中…」にしてタイムアウトを15秒に延ばす
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
            
            # 🎂 誕生月ピックアップ対象かどうかをチェック
            is_pickup = char_name in PICKUP_CHARACTERS
            birthday_mark = "🎂 " if is_pickup else ""

            # キャラ固有のiconが設定されていればそれを優先し、なければレア度標準の絵文字を使う
            char_icon = template.get("icon")
            if char_icon:
                rarity_icon = char_icon
            else:
                rarity_icon = "✨" if template.get("rarity") == "★5" else ("🌟" if template.get("rarity") == "★4" else "")

            existing_char = next((c for c in user_chars if c["name"] == template["name"]), None)

            if existing_char:
                existing_char["count"] = existing_char.get("count", 1) + 1
                existing_char["hp"] += 2
                existing_char["atk"] += 1
                status_note = f"[重複 +1] (所持数: {existing_char['count']})"
            else:
                new_char = {
                    "name": template["name"],
                    "rarity": template.get("rarity", "★3"),
                    "icon": template.get("icon"),
                    "count": 1,
                    "level": 1,
                    "exp": 0,
                    "hp": template.get("hp", 100),
                    "atk": template.get("atk", 10),
                    "spd": template.get("spd", 10),
                    "rec": template.get("rec", 10),
                    "skill_name": template.get("skill_name", "通常攻撃"),
                    "skill_pow": template.get("skill_pow", 1.0),
                }
                user_chars.append(new_char)
                status_note = "**[✨NEW!✨]**"

            # 表示テキストの先頭に birthday_mark (🎂) を追加
            result_lines.append(f"{idx}. {birthday_mark}{rarity_icon} **[{template.get('rarity', '★3')}] {char_name}** {status_note}")

        # --------------------------------------------------
        # 🎰 ガチャ回数のカウント ＆ 実績解除チェック
        # --------------------------------------------------
        u_data["gacha_count"] = u_data.get("gacha_count", 0) + 1
        
        # 3. ガチャ結果を保存
        save_data()

        # 実績の判定（10回以上で解除）
        if u_data["gacha_count"] >= 10:
            await check_and_unlock_achievement(interaction, "gacha_10")

        embed = discord.Embed(
            title="🎰 10連ガチャ結果！",
            description="\n".join(result_lines),
            color=0xFFD700
        )
        embed.set_footer(
            text=f"残高 ｜ 虹の欠片: {items.get('虹の欠片', 0)}個 / ガチャチケ: {items.get('ガチャチケ', 0)}枚"
        )

        # 4. defer() 済みのメッセージを編集して結果を表示する
        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="虹の欠片 1000個で10連", style=discord.ButtonStyle.primary, emoji="💎")
    async def draw_rainbow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "rainbow")

    @discord.ui.button(label="ガチャチケ 10枚で10連", style=discord.ButtonStyle.success, emoji="🎫")
    async def draw_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "ticket")
