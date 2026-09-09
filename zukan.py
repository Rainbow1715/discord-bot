import discord
from discord.ext import commands
import database as db

# --------------------------------------------------
# 📖 キャラ図鑑 View（ページ切り替え対応）
# --------------------------------------------------
class ZukanView(discord.ui.View):
    def __init__(self, user_id: int, all_characters: list, user_char_names: set):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.all_characters = all_characters
        self.user_char_names = user_char_names
        self.current_page = 0
        self.per_page = 5  # 1ページあたり5キャラ表示

        self.update_buttons()

    def update_buttons(self):
        max_page = (len(self.all_characters) - 1) // self.per_page
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= max_page)

    def create_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_chars = self.all_characters[start_idx:end_idx]

        obtained_count = len(self.user_char_names)
        total_count = len(self.all_characters)

        embed = discord.Embed(
            title=f"📖 キャラクター図鑑 ({obtained_count}/{total_count})",
            description=f"コンプリート率: {int(obtained_count / total_count * 100)}%\n" + "─" * 20,
            color=0x3498DB
        )

        for c in page_chars:
            name = c.get("name")
            rarity = c.get("rarity", "★3")
            element = c.get("element", "無")
            role = c.get("role", "不明")

            # ユーザーが持っているか判定
            if name in self.user_char_names:
                icon = c.get("icon", "👤")
                skill = c.get("skill_name", "なし")
                field_value = f"属性: **{element}** | ロール: **{role}**\n必殺技: {skill}"
                field_name = f"{icon} {rarity} {name}"
            else:
                # 未所持の場合
                field_name = f"❓ {rarity} ？？？"
                field_value = "属性: ？？？ | ロール: ？？？\n*（まだ出会っていません）*"

            embed.add_field(name=field_name, value=field_value, inline=False)

        max_page = (len(self.all_characters) - 1) // self.per_page + 1
        embed.set_footer(text=f"ページ {self.current_page + 1} / {max_page}")
        return embed

    @discord.ui.button(label="◀ 前へ", style=discord.ButtonStyle.secondary, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="次へ ▶", style=discord.ButtonStyle.secondary, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

# --------------------------------------------------
# 💬 コマンド部分 (`/zukan` または `!zukan`)
# --------------------------------------------------
@bot.command(name="zukan", aliases=["図鑑"])
async def show_zukan(ctx):
    user_info = db.get_user_profile(ctx.author.id)

    # 全マスターキャラクターのリストを作成（重複排除）
    all_master_chars = []
    seen_names = set()

    # GACHA_POOL と DEFAULT_CHARACTERS の両方をまとめる
    master_sources = db.GACHA_POOL + db.DEFAULT_CHARACTERS
    for c in master_sources:
        if c and c["name"] not in seen_names:
            seen_names.add(c["name"])
            all_master_chars.append(c)

    # レア度順（★5 > ★4 > ★3...）に並び替え
    all_master_chars.sort(key=lambda x: x.get("rarity", "★1"), reverse=True)

    # ユーザーが所持しているキャラ名のセット
    user_char_names = {c["name"] for c in user_info.get("characters", [])}

    view = ZukanView(ctx.author.id, all_master_chars, user_char_names)
    embed = view.create_embed()

    await ctx.send(embed=embed, view=view)
