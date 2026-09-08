import random
import discord
from database import GACHA_POOL, RARITY_RATES, get_user_profile, save_data

def select_character_by_rarity():
    """レア度確率に基づいてキャラを1体抽選する（存在しないレア度は自動フォールバック）"""
    # 1. 重み付きランダムでレア度を決定
    rarities = list(RARITY_RATES.keys())
    weights = list(RARITY_RATES.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    
    # 2. 選ばれたレア度のキャラリストを取得
    pool = [c for c in GACHA_POOL if c.get("rarity") == chosen_rarity]
    
    # 該当レア度のキャラがまだ登録されていない場合は、存在するキャラの中からフォールバック
    if not pool:
        # ★3〜★5などで存在するプールから再選出
        available_rarities = list(set(c.get("rarity") for c in GACHA_POOL))
        chosen_rarity = random.choice(available_rarities)
        pool = [c for c in GACHA_POOL if c.get("rarity") == chosen_rarity]

    # それでも万が一プールが空ならエラー回避用のデフォルトキャラを返す
    if not pool:
        return GACHA_POOL[0] if GACHA_POOL else None
        
def draw_10_gacha():
    """10連ガチャを引く処理"""
    def draw_10_gacha():
        """10連ガチャ（9枠通常 + 1枠★3以上確定枠などの処理例）"""
    results = []
    
    # 通常枠 9連
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

        # 2. 💡 ここで defer() を呼び出し！「考え中…」にしてタイムアウトを15秒に延ばす
        await interaction.response.defer()

        # process_gacha 内のループ処理部分の例
    for template in drawn_templates:
        if not template:
        continue  # None の場合はスキップ
        char_icon = template.get("icon", "❓")

        u_data = get_user_profile(self.user_id)
        items = u_data["items"]

        if cost_type == "rainbow":
            if items.get("虹の欠片", 0) < 1000:
                # defer() 後なので followup で送信します
                await interaction.followup.send("❌ 虹の欠片が足りません！（必要: 1000個）", ephemeral=True)
                return
            items["虹の欠片"] -= 1000
        elif cost_type == "ticket":
            if items.get("ガチャチケ", 0) < 10:
                # defer() 後なので followup で送信します
                await interaction.followup.send("❌ ガチャチケが足りません！（必要: 10枚）", ephemeral=True)
                return
            items["ガチャチケ"] -= 10

        drawn_templates = draw_10_gacha()
        user_chars = u_data["characters"]
        result_lines = []

        for idx, template in enumerate(drawn_templates, start=1):
            # キャラ固有のiconが設定されていればそれを優先し、なければレア度標準の絵文字を使う
            char_icon = template.get("icon")
            if char_icon:
                rarity_icon = char_icon
            else:
                rarity_icon = "✨" if template["rarity"] == "★5" else ("🌟" if template["rarity"] == "★4" else "")
            existing_char = next((c for c in user_chars if c["name"] == template["name"]), None)

            if existing_char:
                existing_char["count"] = existing_char.get("count", 1) + 1
                existing_char["hp"] += 2
                existing_char["atk"] += 1
                status_note = f"**[重複 +1]** (所持数: {existing_char['count']})"
            else:
                new_char = {
                    "name": template["name"],
                    "rarity": template["rarity"],
                    "icon": template.get("icon"),
                    "count": 1,
                    "level": 1,
                    "exp": 0,
                    "hp": template["hp"],
                    "atk": template["atk"],
                    "spd": template["spd"],
                    "rec": template["rec"],
                    "skill_name": template["skill_name"],
                    "skill_pow": template["skill_pow"],
                }
                user_chars.append(new_char)
                status_note = "**[NEW!]**"

            result_lines.append(f"{idx}. {rarity_icon} **[{template['rarity']}] {template['name']}** {status_note}")

        # 3. ガチャ結果を保存
        save_data()

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
