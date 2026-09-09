import discord
from discord import app_commands
from discord.ext import commands
from database import user_data, get_user_profile  # get_user_profileがなければ user_data.get(u_id, {}) でOK


# --------------------------------------------------
# 📖 ページ切り替え用 View
# --------------------------------------------------
class ItemView(discord.ui.View):
    def __init__(self, user: discord.User, u_data: dict):
        super().__init__(timeout=60)
        self.user = user
        self.u_data = u_data
        self.current_page = 1

    def create_embed(self) -> discord.Embed:
        if self.current_page == 1:
            # --------------------------------------------------
            # 📄 ページ1: 主要通貨・チケット
            # --------------------------------------------------
            gold = self.u_data.get("gold", 0)
            items = self.u_data.get("items", {})
            rainbow = items.get("虹の欠片", 0)
            ticket = items.get("ガチャチケット", 0)  # 保存時のキー名に合わせて調整してください

            embed = discord.Embed(
                title=f"🎒 {self.user.display_name} の所持アイテム (1/2)",
                description="現在の所持通貨・チケットです。",
                color=0x3498DB
            )
            embed.add_field(name="💰 ゴールド", value=f"**{gold:,}** G", inline=True)
            embed.add_field(name="💎 虹の欠片", value=f"**{rainbow:,}** 個", inline=True)
            embed.add_field(name="🎫 ガチャチケット", value=f"**{ticket:,}** 枚", inline=False)
            embed.set_footer(text="ページ 1/2 | 下のボタンで切り替え")

        else:
            # --------------------------------------------------
            # 📄 ページ2: 食べ物・消費アイテム
            # --------------------------------------------------
            items = self.u_data.get("items", {})
            
            # 通貨以外のアイテム（食べ物など）を抽出
            exclude_keys = {"虹の欠片", "ガチャチケット"}
            food_items = {k: v for k, v in items.items() if k not in exclude_keys and v > 0}

            embed = discord.Embed(
                title=f"🍱 {self.user.display_name} の所持アイテム (2/2)",
                description="所持している食べ物・消費アイテム一覧です。",
                color=0x2ECC71
            )

            if food_items:
                food_list_str = "\n".join([f"・**{name}**: {count} 個" for name, count in food_items.items()])
                embed.add_field(name="🍔 食べ物・その他", value=food_list_str, inline=False)
            else:
                embed.add_field(name="🍔 食べ物・その他", value="所持している食べ物はありあせん。", inline=False)

            embed.set_footer(text="ページ 2/2 | 下のボタンで切り替え")

        return embed

    @discord.ui.button(label="◀ 1ページ目", style=discord.ButtonStyle.primary, disabled=True)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ 他人のインベントリ操作はできません。", ephemeral=True)
            return

        self.current_page = 1
        # ボタンの有効/無効化切り替え
        self.children[0].disabled = True   # 前へボタン無効化
        self.children[1].disabled = False  # 次へボタン有効化

        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="2ページ目 (食べ物) ▶", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ 他人のインベントリ操作はできません。", ephemeral=True)
            return

        self.current_page = 2
        # ボタンの有効/無効化切り替え
        self.children[0].disabled = False  # 前へボタン有効化
        self.children[1].disabled = True   # 次へボタン無効化

        await interaction.response.edit_message(embed=self.create_embed(), view=self)


# --------------------------------------------------
# 💬 ItemCog (スラッシュコマンド)
# --------------------------------------------------
class ItemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="item", description="所持しているアイテムや通貨を確認します")
    async def item_cmd(self, interaction: discord.Interaction):
        u_data = user_data.get(interaction.user.id, {})
        
        view = ItemView(interaction.user, u_data)
        embed = view.create_embed()
        
        # 本人のみ見れるように ephemeral=True に設定（公開したい場合は除去）
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ItemCog(bot))
