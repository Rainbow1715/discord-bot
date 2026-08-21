import random
import discord
from database import GACHA_POOL, get_user_profile

def draw_10_gacha():
    """10連ガチャを引く処理"""
    results = []
    rarity_weights = [70, 25, 5]  # ★3: 70%, ★4: 25%, ★5: 5%

    star3_pool = [c for c in GACHA_POOL if c["rarity"] == "★3"]
    star4_pool = [c for c in GACHA_POOL if c["rarity"] == "★4"]
    star5_pool = [c for c in GACHA_POOL if c["rarity"] == "★5"]

    for _ in range(10):
        selected_rarity = random.choices(["★3", "★4", "★5"], weights=rarity_weights)[0]
        if selected_rarity == "★3":
            char_template = random.choice(star3_pool)
        elif selected_rarity == "★4":
            char_template = random.choice(star4_pool)
        else:
            char_template = random.choice(star5_pool)

        results.append(char_template)

    return results


class GachaView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def process_gacha(self, interaction: discord.Interaction, cost_type: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーのガチャ画面です。", ephemeral=True)
            return

        u_data = get_user_profile(self.user_id)
        items = u_data["items"]

        if cost_type == "rainbow":
            if items.get("虹の欠片", 0) < 1000:
                await interaction.response.send_message("❌ 虹の欠片が足りません！（必要: 1000個）", ephemeral=True)
                return
            items["虹の欠片"] -= 1000
        elif cost_type == "ticket":
            if items.get("ガチャチケ", 0) < 10:
                await interaction.response.send_message("❌ ガチャチケが足りません！（必要: 10枚）", ephemeral=True)
                return
            items["ガチャチケ"] -= 10

        drawn_templates = draw_10_gacha()
        user_chars = u_data["characters"]
        result_lines = []

        for idx, template in enumerate(drawn_templates, start=1):
            rarity_icon = "✨" if template["rarity"] == "★5" else ("🌟" if template["rarity"] == "★4" else "⚪")
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

        embed = discord.Embed(
            title="🎰 10連ガチャ結果！",
            description="\n".join(result_lines),
            color=0xFFD700
        )
        embed.set_footer(
            text=f"残高 ｜ 虹の欠片: {items.get('虹の欠片', 0)}個 / ガチャチケ: {items.get('ガチャチケ', 0)}枚"
        )

        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="虹の欠片 1000個で10連", style=discord.ButtonStyle.primary, emoji="💎")
    async def draw_rainbow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "rainbow")

    @discord.ui.button(label="ガチャチケ 10枚で10連", style=discord.ButtonStyle.success, emoji="🎫")
    async def draw_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_gacha(interaction, "ticket")
