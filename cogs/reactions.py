import discord
from discord.ext import commands
from discord import app_commands
import database as db

class ReactionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reactions", description="これまでに判明したキャラクターの好物・苦手と反応一覧を表示します")
    async def reactions_command(self, interaction: discord.Interaction):
        # 💡 1. 応答待ち（タイムアウト対策）
        await interaction.response.defer()

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
                    name=f"❔ ？？？",
                    value="【まだこのキャラを持っていません】",
                    inline=False
                )
                continue

            # --------------------------------------------------
            # 所持キャラの反応組み立て処理
            # --------------------------------------------------
            known_likes = u_char.get("known_likes", [])
            known_dislikes = u_char.get("known_dislikes", [])
            
            # 💡 怪しい肉などの特殊反応判定用
            known_special = u_char.get("known_special", [])  # ※データ構造に合わせて調整可

            master_likes = master_char.get("likes", {})
            master_dislikes = master_char.get("dislikes", {})
            master_special = master_char.get("special_reactions", {}) # マスター側の辞書

            # ❤️ 好きな食べ物
            if known_likes:
                like_lines = []
                for food in known_likes:
                    reaction = master_likes.get(food, "「美味しい！」") if isinstance(master_likes, dict) else "「美味しい！」"
                    like_lines.append(f"・**{food}**: {reaction}")
                likes_display = "\n".join(like_lines)
            else:
                likes_display = "まだわかりません"

            # 💔 嫌いな食べ物
            if known_dislikes:
                dislike_lines = []
                for food in known_dislikes:
                    reaction = master_dislikes.get(food, "「……」") if isinstance(master_dislikes, dict) else "「……」"
                    dislike_lines.append(f"・**{food}**: {reaction}")
                dislikes_display = "\n".join(dislike_lines)
            else:
                dislikes_display = "まだわかりません"

            # 🍖 怪しい肉（修正ポイント！）
            # known_likes や known_dislikes、または known_special に「怪しい肉」が含まれているかチェック
            if "怪しい肉" in known_likes or "怪しい肉" in known_dislikes or "怪しい肉" in known_special:
                meat_reaction = master_special.get("怪しい肉") or master_likes.get("怪しい肉") or master_dislikes.get("怪しい肉") or "「……これ、何の肉だ？」"
                meat_display = f"・{meat_reaction}"
            else:
                meat_display = "まだあげたことがありません"

            # 表示テキストの組み立て
            field_value = (
                f"**【好きな食べ物】**\n{likes_display}\n\n"
                f"**【嫌いな食べ物】**\n{dislikes_display}\n\n"
                f"**【怪しい肉】**\n{meat_display}"
            )

            embed.add_field(
                name=f"{char_icon} {char_name}",
                value=field_value,
                inline=False
            )

        # 💡 defer() を使っているため followup.send で送信
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionsCog(bot))
