import discord
from discord.ext import commands
from discord import app_commands
import database as db

class ReactionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reactions", description="これまでに判明したキャラクターの好物・苦手と反応一覧を表示します")
    async def reactions_command(self, interaction: discord.Interaction):
        user_info = db.get_user_profile(interaction.user.id)
        user_chars = user_info.get("characters", [])

        embed = discord.Embed(
            title="📖 判明済み・食べ物の反応図鑑",
            description="これまでに食べ物をあげて判明した反応の一覧です。",
            color=discord.Color.orange()
        )

        for master_char in db.GACHA_POOL:
            char_name = master_char["name"]
            char_icon = master_char.get("icon", "👤")

            u_char = next((c for c in user_chars if c["name"] == char_name), None)

            # --------------------------------------------------
            # 🔒 未所持キャラクターのマスク処理
            # --------------------------------------------------
            if not u_char:
                embed.add_field(
                    name="❔ ？？？",
                    value="【まだこのキャラを持っていません】",
                    inline=False
                )
                continue  # 未所持なので以降の反応組み立て処理をスキップして次のキャラへ

            # --------------------------------------------------
            # 所持キャラの反応組み立て処理（以下は所持している場合のみ実行）
            # --------------------------------------------------
            known_likes = u_char.get("known_likes", [])
            known_dislikes = u_char.get("known_dislikes", [])

            # マスターデータから辞書を取得
            master_likes = master_char.get("likes", {})
            master_dislikes = master_char.get("dislikes", {})

            # ❤️ 好きな食べ物 & 反応の組み立て
            if known_likes:
                like_lines = []
                for food in known_likes:
                    if isinstance(master_likes, dict):
                        reaction = master_likes.get(food, "「美味しい！」")
                    else:
                        reaction = "「美味しい！」"
                    like_lines.append(f"・**{food}**: {reaction}")
                likes_display = "\n".join(like_lines)
            else:
                likes_display = "まだわかりません"

            # 💔 嫌いな食べ物 & 反応の組み立て
            if known_dislikes:
                dislike_lines = []
                for food in known_dislikes:
                    if isinstance(master_dislikes, dict):
                        reaction = master_dislikes.get(food, "「……」")
                    else:
                        reaction = "「……」"
                    dislike_lines.append(f"・**{food}**: {reaction}")
                dislikes_display = "\n".join(dislike_lines)
            else:
                dislikes_display = "まだわかりません"

            # 表示テキストの組み立て
            field_value = (
                f"**【好きな食べ物】**\n{likes_display}\n\n"
                f"**【嫌いな食べ物】**\n{dislikes_display}\n"
            )

            embed.add_field(
                name=f"{char_icon} {char_name}",
                value=field_value,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionsCog(bot))
