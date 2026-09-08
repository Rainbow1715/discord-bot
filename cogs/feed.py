import discord
from discord.ext import commands
from discord import app_commands
import database as db

# --------------------------------------------------
# 🍱 ご飯選択ドロップダウンの View
# --------------------------------------------------
class FoodSelectView(discord.ui.View):
    def __init__(self, user_id: int, target_char_index: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.target_char_index = target_char_index

        user_info = db.get_user_profile(user_id)
        user_items = user_info.get("items", {})

        # 所持しているご飯アイテムのみ抽出
        available_foods = [
            food for food in db.FOOD_ITEMS.keys()
            if user_items.get(food, 0) > 0
        ]

        if not available_foods:
            # ご飯を持っていない場合
            select = discord.ui.Select(
                placeholder="あげるご飯がありません…",
                options=[discord.SelectOption(label="ご飯を持っていません", value="none")],
                disabled=True
            )
            self.add_item(select)
            return

        # ドロップダウンの選択肢を作成（最大25個）
        options = []
        for food_name in available_foods[:25]:
            count = user_items[food_name]
            icon = db.FOOD_ITEMS[food_name].get("icon", "🍱")
            if not icon:
                icon = "🍱"
            
            options.append(
                discord.SelectOption(
                    label=f"{food_name} (所持: {count}個)",
                    value=food_name,
                    emoji=icon if len(icon) == 1 else None
                )
            )

        select = discord.ui.Select(
            placeholder="あげるご飯を選んでね！",
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.food_selected_callback
        self.add_item(select)

    async def food_selected_callback(self, interaction: discord.Interaction):
        # 本人確認
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の操作はできません。", ephemeral=True)
            return

        food_name = self.children[0].values[0]
        if food_name == "none":
            return

        user_info = db.get_user_profile(self.user_id)
        char_data = user_info["characters"][self.target_char_index]

        # 所持数の確認と消費
        if user_info["items"].get(food_name, 0) <= 0:
            await interaction.response.send_message("❌ そのご飯は持っていません！", ephemeral=True)
            return

        user_info["items"][food_name] -= 1

        # データベースのご飯処理を実行
        result = db.feed_character(user_info, char_data, food_name)
        db.save_data()

        # 反応メッセージと演出の組み立て
        taste = result["taste_type"]
        char_name = char_data["name"]

        if taste == "like":
            reaction_msg = f"大喜びしている！✨\n「わーい！ {food_name} 大好き！」"
            color = discord.Color.pink()
        elif taste == "dislike":
            reaction_msg = f"微妙な反応。\n「………」"
            color = discord.Color.dark_gray()
        else:
            reaction_msg = f"おいしそうに食べている！😋\n「もぐもぐ… {food_name} 、ごちそうさま！」"
            color = discord.Color.green()

        embed = discord.Embed(
            title=f"🍱 {char_name} に {food_name} をあげた！",
            description=reaction_msg,
            color=color
        )

        # 獲得した経験値情報
        exp_detail = f"+{result['gained_exp']} XP"
        if result["is_first_time"]:
            exp_detail += " **(★初めてのご飯ボーナス +20XP!)**"

        embed.add_field(name="獲得なつき経験値", value=exp_detail, inline=False)
        embed.add_field(name="現在のなつきLv.", value=f"Lv. {result['current_level']}", inline=True)

        # レベルアップ報酬が発生した場合
        if result["rewards"]:
            reward_str = "\n".join(result["rewards"])
            embed.add_field(name="🎉 なつき度アップ報酬GET！", value=reward_str, inline=False)

        await interaction.response.send_message(embed=embed)


# --------------------------------------------------
# 🎴 キャラカード & 「ご飯をあげる」ボタンの View
# --------------------------------------------------
class CharacterCardView(discord.ui.View):
    def __init__(self, user_id: int, char_index: int, total_chars: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.char_index = char_index
        self.total_chars = total_chars

    @discord.ui.button(label="🍱 ご飯をあげる", style=discord.ButtonStyle.success)
    async def feed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人のキャラカードは操作できません。", ephemeral=True)
            return

        # ご飯選択メニューを表示（ephemeral=True で本人だけにポップアップ表示）
        food_view = FoodSelectView(self.user_id, self.char_index)
        await interaction.response.send_message("🍱 どのアイテムをあげますか？", view=food_view, ephemeral=True)


# --------------------------------------------------
# ⚙️ コマンド Cog 本体
# --------------------------------------------------
class FeedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="chara", description="所持キャラクターの一覧となつき度を確認します")
    async def chara_command(self, interaction: discord.Interaction):
        user_info = db.get_user_profile(interaction.user.id)
        characters = user_info.get("characters", [])

        if not characters:
            await interaction.response.send_message("キャラクターを所持していません。", ephemeral=True)
            return

        # 今回は先頭のキャラクターカードを表示する例（ページ切り替えなども拡張可能です）
        target_index = 0
        char = characters[target_index]

        req_exp = db.get_required_affection_exp(char.get("affection_level", 1))
        
        embed = discord.Embed(
            title=f"{char.get('icon', '')} {char['name']}",
            color=discord.Color.gold()
        )
        embed.add_field(name="レア度", value=char.get("rarity", "★2"), inline=True)
        embed.add_field(name="属性 / 役割", value=f"{char.get('element', '光')} / {char.get('role', 'サポーター')}", inline=True)
        embed.add_field(name="なつき度", value=f"Lv. {char.get('affection_level', 1)} ({char.get('affection_exp', 0)}/{req_exp} XP)", inline=False)

        # 判明済みの好き嫌いリスト表示
        known_likes = "、".join(char.get("known_likes", [])) or "まだ判明していません"
        known_dislikes = "、".join(char.get("known_dislikes", [])) or "まだ判明していません"
        
        embed.add_field(name="❤️ 好きな食べ物（判明済み）", value=known_likes, inline=False)
        embed.add_field(name="💔 嫌いな食べ物（判明済み）", value=known_dislikes, inline=False)

        view = CharacterCardView(interaction.user.id, target_index, len(characters))
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(FeedCog(bot))
