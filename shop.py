import random
import discord
from database import get_user_profile

class ShopView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.button(label="ランダムガチャチケ箱を購入 (1000 G)", style=discord.ButtonStyle.success, emoji="📦")
    async def buy_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーのショップ画面です。", ephemeral=True)
            return

        u_data = get_user_profile(self.user_id)
        if u_data["gold"] < 1000:
            await interaction.response.send_message("❌ ゴールドが足りません！（必要: 1000 G）", ephemeral=True)
            return

        u_data["gold"] -= 1000

        is_jackpot = random.randint(1, 100) == 1
        if is_jackpot:
            tickets = 100
            msg = "🎉🎉 **超大当たり！！** ガチャチケ **100枚** を獲得しました！ 🎉🎉"
            color = 0xFFD700
        else:
            tickets = random.randint(1, 10)
            msg = f"📦 ガチャチケ **{tickets}枚** を獲得しました！"
            color = 0x2ECC71

        items = u_data["items"]
        items["ガチャチケ"] = items.get("ガチャチケ", 0) + tickets

        embed = discord.Embed(
            title="🛍️ 購入完了！",
            description=f"{msg}\n\n💰 所持金: {u_data['gold']} G | 🎫 所持チケット: {items['ガチャチケ']} 枚",
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=None)
