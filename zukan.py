import discord
from discord import app_commands
from discord.ext import commands
import database as db

# 🗡️ 装備マスタをインポート（パスに合わせて調整してください）
from cogs.soubi import EQUIPMENT_MASTER


# --------------------------------------------------
# 📖 キャラ図鑑 View（ページ切り替え対応）
# --------------------------------------------------
class CharacterZukanView(discord.ui.View):
    def __init__(self, user_id: int, all_characters: list, user_char_names: set):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.all_characters = all_characters
        self.user_char_names = user_char_names
        self.current_page = 0
        self.per_page = 5  # 1ページあたり5件

        self.update_buttons()

    def update_buttons(self):
        max_page = max(0, (len(self.all_characters) - 1) // self.per_page)
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= max_page)

    def create_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_chars = self.all_characters[start_idx:end_idx]

        obtained_count = len(self.user_char_names)
        total_count = len(self.all_characters)
        rate = int(obtained_count / total_count * 100) if total_count > 0 else 0

        embed = discord.Embed(
            title=f"📖 キャラクター図鑑 ({obtained_count}/{total_count})",
            description=f"コンプリート率: {rate}%\n" + "─" * 20,
            color=0x3498DB
        )

        for c in page_chars:
            name = c.get("name")
            rarity = c.get("rarity", "★3")
            element = c.get("element", "無")
            role = c.get("role", "不明")

            if name in self.user_char_names:
                icon = c.get("icon", "👤")
                skill = c.get("skill_name", "なし")
                field_value = f"属性: **{element}** | ロール: **{role}**\n必殺技: {skill}"
                field_name = f"{icon} {rarity} {name}"
            else:
                field_name = f"❓ {rarity} ？？？"
                field_value = "属性: ？？？ | ロール: ？？？\n*（まだ出会っていません）*"

            embed.add_field(name=field_name, value=field_value, inline=False)

        max_page = max(1, (len(self.all_characters) - 1) // self.per_page + 1)
        embed.set_footer(text=f"ページ {self.current_page + 1} / {max_page}")
        return embed

    @discord.ui.button(label="◀ 前へ", style=discord.ButtonStyle.secondary, custom_id="prev_page_char")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="次へ ▶", style=discord.ButtonStyle.secondary, custom_id="next_page_char")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)


# --------------------------------------------------
# 🗡️ 装備図鑑 View（ページ切り替え対応）
# --------------------------------------------------
class EquipmentZukanView(discord.ui.View):
    def __init__(self, user_id: int, all_equipments: list, user_equip_names: set):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.all_equipments = all_equipments  # [(eq_name, eq_data), ...] のリスト
        self.user_equip_names = user_equip_names
        self.current_page = 0
        self.per_page = 5

        self.update_buttons()

    def update_buttons(self):
        max_page = max(0, (len(self.all_equipments) - 1) // self.per_page)
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= max_page)

    def create_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_equips = self.all_equipments[start_idx:end_idx]

        obtained_count = len(self.user_equip_names)
        total_count = len(self.all_equipments)
        rate = int(obtained_count / total_count * 100) if total_count > 0 else 0

        embed = discord.Embed(
            title=f"🗡️ 装備図鑑 ({obtained_count}/{total_count})",
            description=f"コンプリート率: {rate}%\n" + "─" * 20,
            color=0xE74C3C
        )

        for eq_name, eq_data in page_equips:
            if eq_name in self.user_equip_names:
                # 所持済みの場合：ステータス ＋ description（解説文）を表示
                stats = []
                if eq_data.get("atk", 0) > 0: stats.append(f"ATK +{eq_data['atk']}")
                if eq_data.get("def", 0) > 0: stats.append(f"DEF +{eq_data['def']}")
                if eq_data.get("p_hp", 0) > 0: stats.append(f"毎ターン回復 +{eq_data['p_hp']}")
                if eq_data.get("stun", 0) > 0: stats.append(f"スタン率 {eq_data['stun']}%")
                
                stats_str = " | ".join(stats) if stats else "特殊効果なし"
                desc_str = eq_data.get("description", "説明文はありません。")
                
                field_name = f"🗡️ {eq_name}"
                field_value = f"**性能**: {stats_str}\n*{desc_str}*"
            else:
                # 未所持の場合
                field_name = "❓ ？？？"
                field_value = "*（まだ手に入れたことがありません）*"

            embed.add_field(name=field_name, value=field_value, inline=False)

        max_page = max(1, (len(self.all_equipments) - 1) // self.per_page + 1)
        embed.set_footer(text=f"ページ {self.current_page + 1} / {max_page}")
        return embed

    @discord.ui.button(label="◀ 前へ", style=discord.ButtonStyle.secondary, custom_id="prev_page_eq")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="次へ ▶", style=discord.ButtonStyle.secondary, custom_id="next_page_eq")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)


# --------------------------------------------------
# 📚 カテゴリ選択 View（最初の画面）
# --------------------------------------------------
class ZukanMainView(discord.ui.View):
    def __init__(self, user_id: int, all_master_chars: list, user_char_names: set, all_equipments: list, user_equip_names: set):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.all_master_chars = all_master_chars
        self.user_char_names = user_char_names
        self.all_equipments = all_equipments
        self.user_equip_names = user_equip_names

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他の人の図鑑は操作できません。", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👤 キャラクター図鑑", style=discord.ButtonStyle.primary)
    async def select_char(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = CharacterZukanView(self.user_id, self.all_master_chars, self.user_char_names)
        await interaction.response.edit_message(embed=view.create_embed(), view=view)

    @discord.ui.button(label="🗡️ 装備図鑑", style=discord.ButtonStyle.success)
    async def select_equip(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = EquipmentZukanView(self.user_id, self.all_equipments, self.user_equip_names)
        await interaction.response.edit_message(embed=view.create_embed(), view=view)


# --------------------------------------------------
# 💬 Cog（コマンド本体）
# --------------------------------------------------
class ZukanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zukan", description="大図鑑（キャラ・装備のコンプリート状況）を確認します")
    async def zukan(self, interaction: discord.Interaction):
        user_info = db.get_user_profile(interaction.user.id)

        # 1. キャラデータ準備
        all_master_chars = []
        seen_names = set()
        master_sources = db.GACHA_POOL + db.DEFAULT_CHARACTERS
        for c in master_sources:
            if c and c.get("name") and c["name"] not in seen_names:
                seen_names.add(c["name"])
                all_master_chars.append(c)

        all_master_chars.sort(key=lambda x: x.get("rarity", "★1"), reverse=True)
        user_char_names = {c["name"] for c in user_info.get("characters", []) if "name" in c}

        # 2. 装備データ準備
        all_equipments = list(EQUIPMENT_MASTER.items())
        
        # 所持品バッグ(items)または装備中の装備から所持済み装備名を取得
        user_items = set(user_info.get("items", {}).keys())
        user_equipped = {c.get("equip") for c in user_info.get("characters", []) if c.get("equip")}
        user_equip_names = (user_items | user_equipped) & set(EQUIPMENT_MASTER.keys())

        # 3. メインビュー表示
        view = ZukanMainView(
            user_id=interaction.user.id,
            all_master_chars=all_master_chars,
            user_char_names=user_char_names,
            all_equipments=all_equipments,
            user_equip_names=user_equip_names
        )

        embed = discord.Embed(
            title="📚 大図鑑メニュー",
            description="確認したい項目を下のボタンから選択してください！",
            color=0xF1C40F
        )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(ZukanCog(bot))
