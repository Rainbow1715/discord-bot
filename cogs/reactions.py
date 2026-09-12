import discord
from discord.ext import commands
from discord import app_commands
import database as db

class ReactionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reactions", description="これまでに判明したキャラクターの好物・苦手と反応一覧を表示します")
    async def reactions_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user_info = db.get_user_profile(interaction.user.id)
        user_chars = user_info.get("characters", [])

        embed = discord.Embed(
            title="📖 判明済み・食べ物の反応図鑑",
            description="これまでに食べ物をあげて判明した反応の一覧です。\n",
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
                    value="【まだこのキャラを持っていません】\n\u200b", # \u200b で次のキャラとの間に余白を作る
                    inline=False
                )
                continue

            # --------------------------------------------------
            # 所持キャラの反応組み立て処理
            # --------------------------------------------------
            known_likes = u_char.get("known_likes", [])
            known_dislikes = u_char.get("known_dislikes", [])
            known_special = u_char.get("known_special", [])

            master_likes = master_char.get("likes", {})
            master_dislikes = master_char.get("dislikes", {})
            master_special = master_char.get("special_reactions", {})

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

            # --------------------------------------------------
            # 🍖 怪しい肉の判定（一番上に配置）
            # --------------------------------------------------
            has_meat_reaction = "怪しい肉" in master_special
            is_meat_revealed = (
                "怪しい肉" in known_special or 
                "怪しい肉" in known_likes or 
                "怪しい肉" in known_dislikes
            )

            sections = []

            # 1. 条件を満たしていれば「怪しい肉」を最優先で追加
            if has_meat_reaction and is_meat_revealed:
                meat_reaction = master_special.get("怪しい肉", "「……これ、何の肉だ？」")
                sections.append(f"**【怪しい肉】**\n・{meat_reaction}")

            # 2. 好きな食べ物
            sections.append(f"**【好きな食べ物】**\n{likes_display}")

            # 3. 嫌いな食べ物
            sections.append(f"**【嫌いな食べ物】**\n{dislikes_display}")

            # 各セクションを改行2つで結合
            field_value = "\n\n".join(sections)

            # 👇 Discordの仕様上、キャラ間の区切り用に末尾にゼロ幅スペース（\u200b）を入れて改行を確保
            field_value += "\n\u200b"

            embed.add_field(
                name=f"{char_icon} {char_name}",
                value=field_value,
                inline=False
            )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionsCog(bot))
