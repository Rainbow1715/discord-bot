import database as db
import discord
from discord import app_commands
from discord.ext import commands


# --------------------------------------------------
# 🔘 ページ切り替え用 View
# --------------------------------------------------
class ReactionPaginationView(discord.ui.View):

    def __init__(self, embeds: list[discord.Embed], author_id: int):
        super().__init__(timeout=180)  # 3分間操作がなければ無効化
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        """現在のページに応じてボタンの有効/無効を更新"""
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.embeds) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """コマンドを実行した本人だけがボタンを操作できるように制限"""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "他の人の図鑑操作はできません！", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="◀ 前へ", style=discord.ButtonStyle.primary, custom_id="prev_page"
    )
    async def prev_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )

    @discord.ui.button(
        label="次へ ▶", style=discord.ButtonStyle.primary, custom_id="next_page"
    )
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )


# --------------------------------------------------
# 📖 コマンド本体
# --------------------------------------------------
class ReactionsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="reactions",
        description="これまでに判明したキャラクターの好物・苦手と反応一覧を表示します",
    )
    async def reactions_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user_info = db.get_user_profile(interaction.user.id)
        user_chars = user_info.get("characters", [])

        embeds = []
        current_embed = discord.Embed(
            title="📖 判明済み・食べ物の反応図鑑",
            description="これまでに食べ物をあげて判明した反応の一覧です。\n",
            color=discord.Color.orange(),
        )
        field_count = 0

        for master_char in db.GACHA_POOL:
            # 6キャラごとに新しいEmbedを作成
            if field_count >= 6:
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title="📖 判明済み・食べ物の反応図鑑",
                    color=discord.Color.orange(),
                )
                field_count = 0

            char_name = master_char["name"]
            char_icon = master_char.get("icon", "👤")

            u_char = next(
                (c for c in user_chars if c["name"] == char_name), None
            )

            # 🔒 未所持キャラクターのマスク処理
            if not u_char:
                current_embed.add_field(
                    name="❔ ？？？",
                    value="【まだこのキャラを持っていません】\n\u200b",
                    inline=False,
                )
                field_count += 1
                continue

            # 所持キャラの反応組み立て
            known_likes = u_char.get("known_likes", [])
            known_dislikes = u_char.get("known_dislikes", [])
            known_special = u_char.get("known_special", [])

            master_likes = master_char.get("likes", {})
            master_dislikes = master_char.get("dislikes", {})
            master_special = master_char.get("special_reactions", {})

            # ❤️ 好きな食べ物（「怪しい肉」を除外）
            filtered_likes = [f for f in known_likes if f != "怪しい肉"]
            if filtered_likes:
                like_lines = []
                for food in filtered_likes:
                    if isinstance(master_likes, dict):
                        reaction = master_likes.get(food, "「美味しい！」")
                    else:
                        reaction = "「美味しい！」"
                    like_lines.append(f"・**{food}**: {reaction}")
                likes_display = "\n".join(like_lines)
            else:
                likes_display = "まだわかりません"

            # 💔 嫌いな食べ物（「怪しい肉」を除外）
            filtered_dislikes = [f for f in known_dislikes if f != "怪しい肉"]
            if filtered_dislikes:
                dislike_lines = []
                for food in filtered_dislikes:
                    if isinstance(master_dislikes, dict):
                        reaction = master_dislikes.get(food, "「……」")
                    elif isinstance(master_dislikes, list) and food in master_dislikes:
                        reaction = "「……」"
                    else:
                        reaction = "「……」"
                    dislike_lines.append(f"・**{food}**: {reaction}")
                dislikes_display = "\n".join(dislike_lines)
            else:
                dislikes_display = "まだわかりません"

            # 🍖 怪しい肉の判定とセリフ取得の柔軟化
            is_meat_revealed = (
                "怪しい肉" in known_special
                or "怪しい肉" in known_likes
                or "怪しい肉" in known_dislikes
            )

            meat_reaction_text = None
            if is_meat_revealed:
                # 1. special_reactions にあればそれを優先
                if "怪しい肉" in master_special:
                    meat_reaction_text = master_special.get("怪しい肉")
                # 2. likes に辞書形式であればそれを取得
                elif isinstance(master_likes, dict) and "怪しい肉" in master_likes:
                    meat_reaction_text = master_likes.get("怪しい肉")
                # 3. dislikes に辞書形式であればそれを取得
                elif isinstance(master_dislikes, dict) and "怪しい肉" in master_dislikes:
                    meat_reaction_text = master_dislikes.get("怪しい肉")
                # 4. どれにもテキストがなければデフォルトメッセージ
                else:
                    meat_reaction_text = "「……これ、何の肉だ？」"

            sections = []

            # 1. 怪しい肉（判明していれば表示）
            if is_meat_revealed and meat_reaction_text:
                sections.append(f"**【怪しい肉】**\n・{meat_reaction_text}")

            # 2. 好きな食べ物
            sections.append(f"**【好きな食べ物】**\n{likes_display}")

            # 3. 嫌いな食べ物
            sections.append(f"**【嫌いな食べ物】**\n{dislikes_display}")

            field_value = "\n\n".join(sections) + "\n\u200b"

            current_embed.add_field(
                name=f"{char_icon} {char_name}",
                value=field_value,
                inline=False,
            )
            field_count += 1

        embeds.append(current_embed)

        # ページ番号をフッターに追加（例：1 / 3 ページ）
        total_pages = len(embeds)
        for i, embed in enumerate(embeds):
            embed.set_footer(text=f"ページ {i + 1} / {total_pages}")

        # 1ページしかない場合はボタンを付けずに送信
        if total_pages == 1:
            await interaction.followup.send(embed=embeds[0])
        else:
            view = ReactionPaginationView(embeds, interaction.user.id)
            await interaction.followup.send(embed=embeds[0], view=view)


async def setup(bot):
    await bot.add_cog(ReactionsCog(bot))
