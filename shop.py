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

    # 🍱 今回追加：ランダムご飯ボックス（800G）
        @discord.ui.button(label="🎁 ランダムご飯ボックス (800G)", style=discord.ButtonStyle.success, row=0)
        async def buy_food_box(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ 他の人のショップは操作できません。", ephemeral=True)
                return

            user_info = db.get_user_profile(self.user_id)
            if user_info["gold"] < 800:
                await interaction.response.send_message("❌ ゴールドが足りません！（必要: 800 G）", ephemeral=True)
                return

            # 800G 消費
            user_info["gold"] -= 800

            # FOOD_ITEMS からランダムに10個（重複あり＝合計10個）抽出
            all_food_names = list(db.FOOD_ITEMS.keys())
            gained_foods = {}

            for _ in range(10):
                chosen = random.choice(all_food_names)
                gained_foods[chosen] = gained_foods.get(chosen, 0) + 1
                user_info["items"][chosen] = user_info["items"].get(chosen, 0) + 1

            db.save_data()

            # 結果表示テキストの組み立て
            result_lines = []
            for food_name, count in gained_foods.items():
                icon = db.FOOD_ITEMS[food_name].get("icon", "🍱")
                if not icon:
                    icon = "🍱"
                result_lines.append(f"・{icon} **{food_name}** x{count}")

            result_msg = "\n".join(result_lines)

            embed = discord.Embed(
                title="🎁 ランダムご飯ボックスを開封した！",
                description=f"合計10個のご飯を手に入れたよ！\n\n{result_msg}",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"残高: {user_info['gold']} G")

            await interaction.response.send_message(embed=embed, ephemeral=True)
