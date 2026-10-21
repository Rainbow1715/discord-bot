import discord
from discord import app_commands
from discord.ext import commands
from database import user_data, get_user_profile, 
# 装備マスターからレア度やアイコンを引くためにインポート
from cogs.soubi import EQUIPMENT_MASTER


# --------------------------------------------------
# 📖 ページ切り替え用 View
# --------------------------------------------------
class ItemView(discord.ui.View):
    def __init__(self, user: discord.User, u_data: dict):
        super().__init__(timeout=60)
        self.user = user
        self.u_data = u_data
        self.current_page = 1
        self.update_button_states()

    def update_button_states(self):
        """現在のページに応じてボタンのラベルと有効/無効を設定"""
        if self.current_page == 1:
            self.children[0].disabled = True
            self.children[0].label = "◀ 前へ"
            self.children[1].disabled = False
            self.children[1].label = "2ページ目 (食べ物) ▶"
        elif self.current_page == 2:
            self.children[0].disabled = False
            self.children[0].label = "◀ 1ページ目 (主要)"
            self.children[1].disabled = False
            self.children[1].label = "3ページ目 (装備) ▶"
        elif self.current_page == 3:
            self.children[0].disabled = False
            self.children[0].label = "◀ 2ページ目 (食べ物)"
            self.children[1].disabled = True
            self.children[1].label = "次へ ▶"

    def create_embed(self) -> discord.Embed:
        if self.current_page == 1:
            # --------------------------------------------------
            # 📄 ページ1: 主要通貨・チケット
            # --------------------------------------------------
            gold = self.u_data.get("gold", 0)
            items = self.u_data.get("items", {})
            rainbow = items.get("虹の欠片", 0)
            ticket = items.get("ガチャチケ", 0)
            soubi_ticket = items.get("装備ガチャチケ", 0)  # 👈 `item` から `items` に修正！

            embed = discord.Embed(
                title=f"🎒 {self.user.display_name} の所持アイテム (1/3)",
                description="現在の所持通貨・チケットです。",
                color=0x3498DB
            )
            embed.add_field(name="💰 ゴールド", value=f"**{gold:,}** G", inline=True)
            embed.add_field(name="💎 虹の欠片", value=f"**{rainbow:,}** 個", inline=True)
            embed.add_field(name="🎫 ガチャチケ", value=f"**{ticket:,}** 枚", inline=True)
            embed.add_field(name="🎟️ 装備ガチャチケ", value=f"**{soubi_ticket:,}** 枚", inline=False)
            embed.set_footer(text="ページ 1/3 | 下のボタンで切り替え")

        elif self.current_page == 2:
            # --------------------------------------------------
            # 📄 ページ2: 食べ物・消費アイテム
            # --------------------------------------------------
            items = self.u_data.get("items", {})
            
            # 通貨以外のアイテム（食べ物など）を抽出
            exclude_keys = {"虹の欠片", "ガチャチケ", "装備ガチャチケ"}
            food_items = {k: v for k, v in items.items() if k not in exclude_keys and v > 0}

            embed = discord.Embed(
                title=f"🍱 {self.user.display_name} の所持アイテム (2/3)",
                description="所持している食べ物・消費アイテム一覧です。",
                color=0x2ECC71
            )

            if food_items:
                food_list_str = "\n".join([f"・**{name}**: {count} 個" for name, count in food_items.items()])
                embed.add_field(name="🍔 食べ物・その他", value=food_list_str, inline=False)
            else:
                embed.add_field(name="🍔 食べ物・その他", value="所持している食べ物はありません。", inline=False)

            embed.set_footer(text="ページ 2/3 | 下のボタンで切り替え")

        else:
            # --------------------------------------------------
            # 📄 ページ3: 所持装備品一覧（辞書型のストック管理に対応）
            # --------------------------------------------------
            from database import _normalize_equipments
            raw_eq = self.u_data.get("equipments", {})
            equip_dict = _normalize_equipments(raw_eq)  # {"装備名": 個数} の辞書に変換

            embed = discord.Embed(
                title=f"🗡️ {self.user.display_name} の所持装備 (3/3)",
                description="所持している装備品一覧です。",
                color=0xE74C3C
            )

            if equip_dict:
                equip_lines = []
                for eq_name, count in equip_dict.items():
                    if count <= 0:
                        continue
                    # 装備マスターから情報を引く（アイコンやレア度）
                    eq_master = EQUIPMENT_MASTER.get(eq_name, {})
                    icon = eq_master.get("icon", "⚔️")
                    rarity = eq_master.get("rarity", 3)
                    rarity_str = f"★{rarity}" if str(rarity).isdigit() else str(rarity)
                    
                    equip_lines.append(f"・{icon} **{eq_name}** [{rarity_str}] ×{count}個")

                if equip_lines:
                    embed.add_field(name="⚔️ 装備品", value="\n".join(equip_lines), inline=False)
                else:
                    embed.add_field(name="⚔️ 装備品", value="所持している装備はありません。", inline=False)
            else:
                embed.add_field(name="⚔️ 装備品", value="所持している装備はありません。", inline=False)

            embed.set_footer(text="ページ 3/3 | 下のボタンで切り替え")

        return embed

    @discord.ui.button(label="◀ 前へ", style=discord.ButtonStyle.primary, disabled=True)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ 他人のインベントリ操作はできません。", ephemeral=True)
            return

        if self.current_page > 1:
            self.current_page -= 1
        
        self.update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="次へ ▶", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ 他人のインベントリ操作はできません。", ephemeral=True)
            return

        if self.current_page < 3:
            self.current_page += 1

        self.update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)


# --------------------------------------------------
# 💬 ItemCog (スラッシュコマンド)
# --------------------------------------------------
class ItemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="item", description="所持しているアイテムや通貨を確認します")
    async def item_cmd(self, interaction: discord.Interaction):
        # 確実に最新のプロフィールデータを取得するために get_user_profile を使用
        u_data = get_user_profile(interaction.user.id)
        
        view = ItemView(interaction.user, u_data)
        embed = view.create_embed()
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ItemCog(bot))
