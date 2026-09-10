import discord
from discord.ext import commands
from discord import app_commands
import database as db

class ReactionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reactions", description="これまでに判明したキャラクターの好物・苦手と反応一覧を表示します")
    async def reactions_command(self, interaction: discord.Interaction):
        # ユーザーデータの取得
        user_info = db.get_user_profile(interaction.user.id)
        user_chars = user_info.get("characters", [])

        embed = discord.Embed(
            title="📖 判明済み・食べ物の反応図鑑",
            description="これまでに食べ物をあげて判明した反応の一覧です。",
            color=discord.Color.orange()
        )

        # GACHA_POOL内の全マスターキャラを順番にチェック
        for master_char in db.GACHA_POOL:
            char_name = master_char["name"]
            char_icon = master_char.get("icon", "👤")

            # ユーザーの所持キャラデータから判明済みリストを取得（未所持の場合は空リスト）
            u_char = next((c for c in user_chars if c["name"] == char_name), None)
            known_likes = u_char.get("known_likes", []) if u_char else []
            known_dislikes = u_char.get("known_dislikes", []) if u_char else []

            # --------------------------------------------------
            # ❤️ 好きな食べ物 & 反応の判定
            # --------------------------------------------------
            if known_likes:
                likes_str = "、".join(known_likes)
                # マスターデータからセリフを取得（設定がなければデフォルトセリフ）
                like_reaction = master_char.get("like_reaction", "「わーい！ありがとう！」")
            else:
                likes_str = "まだわかりません"
                like_reaction = "まだわかりません"

            # --------------------------------------------------
            # 💔 嫌いな食べ物 & 反応の判定
            # --------------------------------------------------
            if known_dislikes:
                dislikes_str = "、".join(known_dislikes)
                # マスターデータからセリフを取得（設定がなければデフォルトセリフ）
                dislike_reaction = master_char.get("dislike_reaction", "「……」")
            else:
                dislikes_str = "まだわかりません"
                dislike_reaction = "まだわかりません"

            # 表示テキストの組み立て
            field_value = (
                f"**好きな食べ物** / {likes_str}\n"
                f"└ *食べた時の反応*: {like_reaction}\n"
                f"**嫌いな食べ物** / {dislikes_str}\n"
                f"└ *食べた時の反応*: {dislike_reaction}"
            )

            embed.add_field(
                name=f"【{char_icon} {char_name}】",
                value=field_value,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionsCog(bot))
