import discord
from discord import app_commands

# 👑 あなたのDiscordユーザーID（数値）
ADMIN_ID = 837631984280666162

def is_admin():
    """管理者チェック用のデコレータ（admin.py と同じ形式）"""
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

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        role = guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message(
                "❌ このロールはすでに削除されているか、見つかりませんでした。",
                ephemeral=True
            )
            return

        # 🔒 本人にしか見えない（ephemeral=True）トグル処理
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                f"🔒 ロール **{role.name}** を外しました。",
                ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"✨ ロール **{role.name}** を付与しました！",
                ephemeral=True
            )


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
    description="【管理者】作成済みの役職パネルの内容変更やボタン追加を行います"
)
@app_commands.describe(
    message_id="編集したいパネルのメッセージID",
    channel="パネルが置かれているチャンネル",
    new_title="新しいタイトル（変更しない場合は空欄）",
    new_description="新しい説明文（変更しない場合は空欄）",
    add_role="追加で配置したいロール（任意）",
    add_button_label="追加するボタンのテキスト（ロール指定時必須）",
    add_button_emoji="追加するボタンの絵文字（任意）",
    add_button_style="追加するボタンの色"
)
@app_commands.choices(add_button_style=[
    app_commands.Choice(name="青 (Primary)", value="primary"),
    app_commands.Choice(name="灰色 (Secondary)", value="secondary"),
    app_commands.Choice(name="緑 (Success)", value="success"),
    app_commands.Choice(name="赤 (Danger)", value="danger"),
])
@is_admin()
async def edit_panel(
    interaction: discord.Interaction,
    message_id: str,
    channel: discord.TextChannel,
    new_title: str = None,
    new_description: str = None,
    add_role: discord.Role = None,
    add_button_label: str = None,
    add_button_emoji: str = None,
    add_button_style: str = "primary"
):
    try:
        target_message = await channel.fetch_message(int(message_id))
    except Exception:
        await interaction.response.send_message("❌ 指定されたメッセージが見つかりませんでした。IDとチャンネルを確認してください。", ephemeral=True)
        return

    if not target_message.embeds:
        await interaction.response.send_message("❌ 指定されたメッセージはパネル（Embed）ではありません。", ephemeral=True)
        return

    # 1. Embed（テキスト）の書き換え
    old_embed = target_message.embeds[0]
    new_embed = discord.Embed(
        title=new_title if new_title else old_embed.title,
        description=new_description if new_description else old_embed.description,
        color=old_embed.color
    )
    new_embed.set_footer(text=old_embed.footer.text if old_embed.footer else "下のボタンを押すとロールの取得・解除ができます。")

    # 2. View（ボタン）の更新・追加
    view = discord.ui.View.from_message(target_message)
    if view is None:
        view = CustomRolePanelView()

    # ロールボタンの追加指定がある場合
    if add_role:
        if not add_button_label:
            await interaction.response.send_message("❌ 新しいロールボタンを追加するには `add_button_label`（ボタンテキスト）も指定してください。", ephemeral=True)
            return

        bot_member = interaction.guild.me
        if add_role >= bot_member.top_role:
            await interaction.response.send_message(f"❌ Botの役職位置が指定したロール（{add_role.name}）より下にあるため付与できません。", ephemeral=True)
            return

        style_map = {
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger
        }
        btn_style = style_map.get(add_button_style, discord.ButtonStyle.primary)

        # 既存のViewに新しいボタンを追加
        view.add_item(CustomRoleButton(
            role_id=add_role.id,
            label=add_button_label,
            emoji=add_button_emoji,
            style=btn_style
        ))

    # パネルメッセージを編集・更新
    await target_message.edit(embed=new_embed, view=view)
    await interaction.response.send_message("✅ 役職パネルを更新しました！", ephemeral=True)


# --------------------------------------------------
# 🔌 setup 関数（admin.py と同じ登録方式）
# --------------------------------------------------
async def setup(bot):
    bot.tree.add_command(create_panel)
    bot.tree.add_command(edit_panel)

# 2. ⚠️ 超重要：Bot再起動後も既存のボタンが動き続けるようにするための永続ビューを登録
    # これがないと、古いボタンを押したときにコールバックが見つからずエラーになります
    bot.add_view(CustomRolePanelView())
