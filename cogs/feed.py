import discord
from discord.ext import commands
from discord import app_commands
import database as db
import achievement

EAT_ACHIEVEMENT_MAP = {
    "竹村しえら": "eat_siera",
    "れーちゃん": "eat_retyan",
    "レオ": "eat_reo",
    "Gerânio": "eat_touwata",
    "白黒レイ": "eat_skrei",
    "茉鈴": "eat_marin",
    "橘柊人": "eat_syuuto",
    "河野蜜柑": "eat_mikan",
    "ロイ": "eat_roi",
    "折原和也": "eat_orihara",
    "神明龍矢": "eat_tatuya",
    "サラ": "eat_sara",
}

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

        # ターゲットキャラのデータを取得して「食べたことのあるご飯リスト」を取得
        characters = user_info.get("characters", [])
        eaten_foods = []
        if target_char_index < len(characters):
            eaten_foods = characters[target_char_index].get("eaten_foods", [])

        # 所持しているご飯アイテムのみ抽出
        available_foods = [
            food for food in db.FOOD_ITEMS.keys()
            if user_items.get(food, 0) > 0
        ]

        if not available_foods:
            select = discord.ui.Select(
                placeholder="あげるご飯がありません…",
                options=[discord.SelectOption(label="ご飯を持っていません", value="none")],
                disabled=True
            )
            self.add_item(select)
            return

        options = []
        for food_name in available_foods[:25]:
            count = user_items[food_name]
            icon = db.FOOD_ITEMS[food_name].get("icon", "🍱")
            if not icon:
                icon = "🍱"
            
            label = f"{food_name} (所持: {count}個)"
            
            # ⭕️ 「あげたことがある場合」のみ説明文を付与
            if food_name in eaten_foods:
                description = "✅ あげたことがあります"
            else:
                description = None

            options.append(
                discord.SelectOption(
                    label=label,
                    value=food_name,
                    description=description,
                    emoji=icon
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
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の操作はできません。", ephemeral=True)
            return

        food_name = self.children[0].values[0]
        if food_name == "none":
            return

        # 3秒タイムアウトを防ぐため応答を保留
        await interaction.response.defer()

        user_info = db.get_user_profile(self.user_id)
        
        if self.target_char_index >= len(user_info["characters"]):
            await interaction.followup.send("❌ キャラクターデータが見つかりません。", ephemeral=True)
            return

        char_data = user_info["characters"][self.target_char_index]

        if user_info["items"].get(food_name, 0) <= 0:
            await interaction.followup.send("❌ そのご飯は持っていません！", ephemeral=True)
            return

        # 🍶 1回だけ処理を実行（お酒NGなどのチェックも内部で行われる）
        result = db.feed_character(user_info, char_data, food_name)

        # 🚫 お酒NGなどのエラーが発生した場合は消費せずに中断
        if result.get("status") == "error":
            await interaction.followup.send(result["message"], ephemeral=True)
            return
            
        # ✅ 成功した場合のみ、アイテムを1つ減らして保存
        user_info["items"][food_name] -= 1
        db.save_data()

        taste = result["taste_type"]
        char_name = char_data["name"]

        if taste == "like":
            reaction_msg = f"大喜びしている！✨\n「わーい！ {food_name} 大好き！」"
            color = discord.Color.pink()
        elif taste == "dislike":
            reaction_msg = f"微妙な表情。\n「……」"
            color = discord.Color.dark_gray()
            # 🔻 💔 嫌いなものを食べた時の実績チェック（ここを追加！）
            ach_id = EAT_ACHIEVEMENT_MAP.get(char_name)
            if ach_id:
                await achievements.check_and_unlock_achievement(interaction, ach_id)
        else:
            reaction_msg = f"おいしそうに食べている！😋\n「もぐもぐ… {food_name} 、ごちそうさま！」"
            color = discord.Color.green()

        embed = discord.Embed(
            title=f"🍱 {char_name} に {food_name} をあげた！",
            description=reaction_msg,
            color=color
        )

        exp_detail = f"+{result['gained_exp']} XP"
        if result.get("is_first_time"):
            exp_detail += " **(★初めてのご飯ボーナス +20XP!)**"

        embed.add_field(name="獲得なつき経験値", value=exp_detail, inline=False)
        embed.add_field(name="現在のなつきLv.", value=f"Lv. {result['current_level']}", inline=True)

        if result.get("rewards"):
            reward_str = "\n".join(result["rewards"])
            embed.add_field(name="🎉 なつき度アップ報酬GET！", value=reward_str, inline=False)

        await interaction.followup.send(embed=embed)


# --------------------------------------------------
# 🎴 キャラカード & 「ご飯をあげる」ボタンの View
# --------------------------------------------------
class CharacterCardView(discord.ui.View):
    def __init__(self, user_id: int, char_index: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.char_index = char_index

    @discord.ui.button(label="🍱 ご飯をあげる", style=discord.ButtonStyle.success)
    async def feed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人のキャラカードは操作できません。", ephemeral=True)
            return

        # 3秒タイムアウトを防ぐため先に即時応答（defer）を入れる
        await interaction.response.defer(ephemeral=True)

        food_view = FoodSelectView(self.user_id, self.char_index)
        await interaction.followup.send("🍱 どのアイテムをあげますか？", view=food_view, ephemeral=True)


# --------------------------------------------------
# ⚙️ コマンド Cog 本体
# --------------------------------------------------
class FeedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="chara", description="所持キャラクターの一覧となつき度を確認します")
    @app_commands.describe(name="確認したいキャラクターの名前（一部でもOK）")
    async def chara_command(self, interaction: discord.Interaction, name: str = None):
        user_info = db.get_user_profile(interaction.user.id)
        characters = user_info.get("characters", [])

        if not characters:
            await interaction.response.send_message("キャラクターを所持していません。", ephemeral=True)
            return

        # 名前が指定されていない場合は所持キャラ一覧リストを表示
        if not name:
            char_list_str = "\n".join([f"・{c['name']} (Lv.{c.get('level', 1)})" for c in characters])
            embed = discord.Embed(
                title=f"👥 {interaction.user.display_name} の所持キャラ一覧",
                description=f"{char_list_str}\n\n💡 `/chara 名前` で特定のキャラカードを開いてご飯をあげられます！",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return

        # 🔍 名前での検索処理（部分一致）
        matched_chars = []
        for idx, char in enumerate(characters):
            if name.lower() in char["name"].lower():
                matched_chars.append((idx, char))

        # 該当なしの場合
        if not matched_chars:
            await interaction.response.send_message(f"❌ 「{name}」に一致する所持キャラクターが見つかりませんでした。", ephemeral=True)
            return

        # 複数ヒットした場合
        if len(matched_chars) > 1:
            candidates_str = "\n".join([f"・{char['name']}" for _, char in matched_chars])
            await interaction.response.send_message(
                f"🔍 候補が複数いるよ！\n{candidates_str}\n\nもう少し詳しく名前を入力してみてね！",
                ephemeral=True
            )
            return

        # 1体だけに特定できた場合
        target_index, char = matched_chars[0]
        req_exp = db.get_required_affection_exp(char.get("affection_level", 1))

        embed = discord.Embed(
            title=f"{char.get('icon', '')} {char['name']}",
            color=discord.Color.gold()
        )
        embed.add_field(name="レア度", value=char.get("rarity", "★2"), inline=True)
        embed.add_field(name="属性 / 役割", value=f"{char.get('element', '光')} / {char.get('role', 'サポーター')}", inline=True)
        embed.add_field(name="なつき度", value=f"Lv. {char.get('affection_level', 1)} ({char.get('affection_exp', 0)}/{req_exp} XP)", inline=False)

        known_likes = "、".join(char.get("known_likes", [])) or "まだ判明していません"
        known_dislikes = "、".join(char.get("known_dislikes", [])) or "まだ判明していません"

        embed.add_field(name="❤️ 好きな食べ物（判明済み）", value=known_likes, inline=False)
        embed.add_field(name="💔 嫌いな食べ物（判明済み）", value=known_dislikes, inline=False)

        view = CharacterCardView(interaction.user.id, target_index)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(FeedCog(bot))
