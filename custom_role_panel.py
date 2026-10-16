import discord
from discord import app_commands
from discord.ext import commands

# --------------------------------------------------
# 🎛️ 動的・永続ボタン用の View クラス
# --------------------------------------------------
class CustomRoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str = None, style: discord.ButtonStyle = discord.ButtonStyle.primary):
        # custom_id に role_id を埋め込むことで、再起動後もどのロールを付与すればいいか判定できるようにする
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

        # トグル形式（持っていれば外し、持っていなければ付与）
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            # 👇 ephemeral=True が付いているため、押した本人にしか見えません！
            await interaction.response.send_message(
                f"🔒 ロール **{role.name}** を外しました。",
                ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            # 👇 こちらも本人限定の通知です！
            await interaction.response.send_message(
                f"✨ ロール **{role.name}** を付与しました！",
                ephemeral=True
            )


class CustomRolePanelView(discord.ui.View):
    def __init__(self, role_id: int, label: str, emoji: str = None, style_name: str = "primary"):
        super().__init__(timeout=None) # 永続化

        # スタイルの文字列を Discord の ButtonStyle に変換
        style_map = {
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger
        }
        btn_style = style_map.get(style_name, discord.ButtonStyle.primary)

        # ボタンを追加
        self.add_item(CustomRoleButton(role_id=role_id, label=label, emoji=emoji, style=btn_style))


# --------------------------------------------------
# 🤖 コグの定義
# --------------------------------------------------
class CustomRolePanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ※ データベースやJSONに保存していない場合、過去に作ったパネルのボタンを完全復元するには
        # 起動時にすべてのロールIDを保持させる必要がありますが、
        # まずはシンプルにコマンドで作成・動作する基本形にしています。

    @app_commands.command(
        name="create_panel",
        description="【管理者用】指定したロールを付与できるボタンパネルを作成します"
    )
    @app_commands.describe(
        channel="パネルを送信するチャンネル",
        title="パネルのタイトル",
        description="パネルの説明文",
        role="付与・解除させたいロール",
        button_label="ボタンに表示するテキスト",
        button_emoji="ボタンにつける絵文字（オプション）",
        button_style="ボタンの色（primary, secondary, success, danger）"
    )
    @app_commands.choices(button_style=[
        app_commands.Choice(name="青 (Primary)", value="primary"),
        app_commands.Choice(name="灰色 (Secondary)", value="secondary"),
        app_commands.Choice(name="緑 (Success)", value="success"),
        app_commands.Choice(name="赤 (Danger)", value="danger"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def create_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        role: discord.Role,
        button_label: str,
        button_emoji: str = None,
        button_style: str = "primary"
    ):
        # 1. 権限チェック（Bot自身がそのロールを付与できる権限を持っているか）
        bot_member = interaction.guild.me
        if role >= bot_member.top_role:
            await interaction.response.send_message(
                f"❌ Botの役職位置が指定したロール（{role.name}）より下にあるため、このロールを付与できません。サーバー設定の「役職」でBotの位置を上に動かしてください。",
                ephemeral=True
            )
            return

        # 2. Embed（見た目）の作成
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x3498DB
        )
        embed.set_footer(text="下のボタンを押すとロールの取得・解除ができます。")

        # 3. ボタン付きビューの作成
        view = CustomRolePanelView(
            role_id=role.id,
            label=button_label,
            emoji=button_emoji,
            style_name=button_style
        )

        # 4. 指定チャンネルに送信
        await channel.send(embed=embed, view=view)

        # 5. 実行者に完了通知
        await interaction.response.send_message(
            f"✅ {channel.mention} にロールパネルを設置しました！",
            ephemeral=True
        )

    # 権限エラーなどの処理
    @create_panel.error
    async def create_panel_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ このコマンドを実行する権限がありません（管理者限定）。", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ エラーが発生しました: {error}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CustomRolePanelCog(bot))
