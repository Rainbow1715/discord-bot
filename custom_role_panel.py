import discord
from discord import app_commands

ADMIN_ID = 837631984280666162

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ このコマンドは管理者専用です。", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

# --------------------------------------------------
# 🎛️ 動的・永続ボタン用の View クラス
# --------------------------------------------------
class CustomRoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str = None, style: discord.ButtonStyle = discord.ButtonStyle.primary):
        super().__init__(
            label=label,
            emoji=emoji,
            style=style,
            custom_id=f"role_panel_{role_id}"
        )
        self.role_id = role_id

    # 💡 callback はここから完全に削除しました！


class CustomRolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 永続化

    def add_role_button(self, role_id: int, label: str, emoji: str = None, style_name: str = "primary"):
        style_map = {
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger
        }
        btn_style = style_map.get(style_name, discord.ButtonStyle.primary)
        self.add_item(CustomRoleButton(role_id=role_id, label=label, emoji=emoji, style=btn_style))


# --------------------------------------------------
# 1. 役職パネル新規作成コマンド (/create_panel)
# --------------------------------------------------
@app_commands.command(
    name="create_panel",
    description="【管理者】指定したロールを付与できるボタンパネルを作成します"
)
@app_commands.describe(
    channel="パネルを送信するチャンネル",
    title="パネルのタイトル",
    description="パネルの説明文",
    role="付与・解除させたいロール",
    button_label="ボタンに表示するテキスト",
    button_emoji="ボタンにつける絵文字（任意）",
    button_style="ボタンの色（primary, secondary, success, danger）"
)
@app_commands.choices(button_style=[
    app_commands.Choice(name="青 (Primary)", value="primary"),
    app_commands.Choice(name="灰色 (Secondary)", value="secondary"),
    app_commands.Choice(name="緑 (Success)", value="success"),
    app_commands.Choice(name="赤 (Danger)", value="danger"),
])
@is_admin()
async def create_panel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str,
    description: str,
    role: discord.Role,
    button_label: str,
    button_emoji: str = None,
    button_style: str = "primary"
):
    bot_member = interaction.guild.me
    if role >= bot_member.top_role:
        await interaction.response.send_message(
            f"❌ Botの役職位置が指定したロール（{role.name}）より下にあるため付与できません。サーバー設定でBotの役職を上に移動してください。",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=0x3498DB
    )
    embed.set_footer(text="下のボタンを押すとロールの取得・解除ができます。")

    view = CustomRolePanelView()
    view.add_role_button(
        role_id=role.id,
        label=button_label,
        emoji=button_emoji,
        style_name=button_style
    )

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(
        f"✅ {channel.mention} にロールパネルを作成しました！",
        ephemeral=True
    )


# --------------------------------------------------
# 2. 既存パネル編集コマンド (/edit_panel)
# --------------------------------------------------
@app_commands.command(
    name="edit_panel",
    description="【管理者】作成済みの役職パネルの内容変更や、複数の新しいボタンの同時追加を行います"
)
@app_commands.describe(
    message_id="編集したいパネルのメッセージID",
    channel="パネルが置かれているチャンネル",
    new_title="新しいタイトル（変更しない場合は空欄）",
    new_description="新しい説明文（変更しない場合は空欄）",
    role_1="追加ロール1（任意）", label_1="追加ボタン1のテキスト", button_emoji_1="ボタンにつける絵文字（任意）", style_1="追加ボタン1の色",
    role_2="追加ロール2（任意）", label_2="追加ボタン2のテキスト", button_emoji_2="ボタンにつける絵文字（任意）", style_2="追加ボタン2の色",
    role_3="追加ロール3（任意）", label_3="追加ボタン3のテキスト", button_emoji_3="ボタンにつける絵文字（任意）", style_3="追加ボタン3の色",
)
@app_commands.choices(
    style_1=[
        app_commands.Choice(name="青 (Primary)", value="primary"),
        app_commands.Choice(name="灰色 (Secondary)", value="secondary"),
        app_commands.Choice(name="緑 (Success)", value="success"),
        app_commands.Choice(name="赤 (Danger)", value="danger"),
    ],
    style_2=[
        app_commands.Choice(name="青 (Primary)", value="primary"),
        app_commands.Choice(name="灰色 (Secondary)", value="secondary"),
        app_commands.Choice(name="緑 (Success)", value="success"),
        app_commands.Choice(name="赤 (Danger)", value="danger"),
    ],
    style_3=[
        app_commands.Choice(name="青 (Primary)", value="primary"),
        app_commands.Choice(name="灰色 (Secondary)", value="secondary"),
        app_commands.Choice(name="緑 (Success)", value="success"),
        app_commands.Choice(name="赤 (Danger)", value="danger"),
    ],
)
@is_admin()
async def edit_panel(
    interaction: discord.Interaction,
    message_id: str,
    channel: discord.TextChannel,
    new_title: str = None,
    new_description: str = None,
    role_1: discord.Role = None, label_1: str = None, button_emoji_1: str = None, style_1: str = "primary",
    role_2: discord.Role = None, label_2: str = None, button_emoji_2: str = None, style_2: str = "primary",
    role_3: discord.Role = None, label_3: str = None, button_emoji_3: str = None, style_3: str = "primary",
):
    try:
        target_message = await channel.fetch_message(int(message_id))
    except Exception:
        await interaction.response.send_message("❌ 指定されたメッセージが見つかりませんでした。IDとチャンネルを確認してください。", ephemeral=True)
        return

    if not target_message.embeds:
        await interaction.response.send_message("❌ 指定されたメッセージはパネル（Embed）ではありません。", ephemeral=True)
        return

    old_embed = target_message.embeds[0]
    new_embed = discord.Embed(
        title=new_title if new_title else old_embed.title,
        description=new_description if new_description else old_embed.description,
        color=old_embed.color
    )
    new_embed.set_footer(text=old_embed.footer.text if old_embed.footer else "下のボタンを押すとロールの取得・解除ができます。")

    new_view = CustomRolePanelView()
    if target_message.components:
        for action_row in target_message.components:
            for child in action_row.children:
                if isinstance(child, discord.Button):
                    if child.custom_id and child.custom_id.startswith("role_panel_"):
                        try:
                            r_id = int(child.custom_id.replace("role_panel_", ""))
                            style_str_map = {
                                discord.ButtonStyle.primary: "primary",
                                discord.ButtonStyle.secondary: "secondary",
                                discord.ButtonStyle.success: "success",
                                discord.ButtonStyle.danger: "danger"
                            }
                            s_name = style_str_map.get(child.style, "primary")
                            emoji_str = str(child.emoji) if child.emoji else None

                            new_view.add_role_button(
                                role_id=r_id,
                                label=child.label or "ロール",
                                emoji=emoji_str,
                                style_name=s_name
                            )
                        except ValueError:
                            pass

    add_targets = [
        (role_1, label_1, button_emoji_1, style_1),
        (role_2, label_2, button_emoji_2, style_2),
        (role_3, label_3, button_emoji_3, style_3),
    ]

    bot_member = interaction.guild.me
    for r, lbl, emo, stl in add_targets:
        if r:
            if not lbl:
                await interaction.response.send_message(f"❌ 追加するロール「{r.name}」に対して、対応するボタンのテキスト（label）が入力されていません。", ephemeral=True)
                return
            if r >= bot_member.top_role:
                await interaction.response.send_message(f"❌ Botの役職位置が指定したロール（{r.name}）より下にあるため付与できません。", ephemeral=True)
                return

            new_view.add_role_button(
                role_id=r.id,
                label=lbl,
                emoji=emo,
                style_name=stl
            )

    await target_message.edit(embed=new_embed, view=new_view)
    await interaction.response.send_message("✅ 役職パネルを更新し、指定したロールボタンを追加しました！", ephemeral=True)

# --------------------------------------------------
# 🔌 setup 関数
# --------------------------------------------------
async def setup(bot):
    bot.tree.add_command(create_panel)
    bot.tree.add_command(edit_panel)
    bot.add_view(CustomRolePanelView())
