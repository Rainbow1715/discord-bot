import discord
from discord import app_commands
from discord.ext import commands
import database as db


class CharacterConvertView(discord.ui.View):
    def __init__(self, user_id: int, max_lb_chars: list):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.max_lb_chars = max_lb_chars  # 凸が+5以上のキャラクターのリスト
        self.selected_char_name = None

        self.update_select()

    def update_select(self):
        # 既存のSelectメニューがあればクリアして再追加
        for item in list(self.children):
            if getattr(item, "is_convert_select", False):
                self.remove_item(item)

        options = []
        for c in self.max_lb_chars[:25]:  # Discordのドロップダウン上限25個
            name = c.get("name")
            rarity = c.get("rarity", "★3")
            lb = c.get("limit_break", 5)
            options.append(
                discord.SelectOption(
                    label=f"[{rarity}] {name} (凸+{lb})",
                    value=name,
                    description="このキャラを輝石に変換します"
                )
            )

        if not options:
            options.append(discord.SelectOption(label="変換できるキャラがいません", value="NONE"))

        select = discord.ui.Select(
            placeholder="💎 輝石に変換するキャラクターを選択",
            options=options,
            custom_id="select_convert_char",
            row=0
        )
        select.is_convert_select = True
        select.callback = self.on_select
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーの画面です。", ephemeral=True)
            return False
        return True

    async def on_select(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, discord.ui.Select) and child.custom_id == "select_convert_char":
                if child.values and child.values[0] != "NONE":
                    self.selected_char_name = child.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="決定（余剰分をすべて輝石に変換）", style=discord.ButtonStyle.danger, emoji="♻️", row=1)
    async def confirm_convert(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_char_name:
            await interaction.response.send_message("⚠️ 変換するキャラクターを選択してください！", ephemeral=True)
            return

        u_data = db.get_user_profile(self.user_id)
        user_chars = u_data.setdefault("characters", [])

        # 対象のキャラクターを検索
        target_char = next((c for c in user_chars if c.get("name") == self.selected_char_name), None)

        if not target_char or target_char.get("limit_break", 0) < 5:
            await interaction.response.send_message("❌ 対象のキャラクターが見つからないか、完凸(+5以上)していません。", ephemeral=True)
            return

        current_count = target_char.get("count", 1)
        
        # 本体（1体）を除いた余剰分を計算
        surplus_count = current_count - 1

        if surplus_count > 0:
            # 本体1体を残して、余剰分をすべて輝石に変換
            target_char["count"] = 1  5以上の完凸でも本体1体にするか、それとも limit_break 達成後さらに増えた分だけか？
            # ※もし「完凸（limit_break >= 5）になったあとにガチャで引いた分」をすべて輝石にする場合は、
            # カウント管理の仕様に合わせて調整します。
        
        # もし count が 1 より多い（余剰がある）場合、または個別に管理している場合
        if current_count > 1:
            # 余剰分から1つ減らす
            target_char["count"] = current_count - 1
            
            # 輝石を付与
            items = u_data.setdefault("items", {})
            items["輝石"] = items.get("輝石", 0) + 1
            db.save_data()

            await interaction.response.send_message(
                f"♻️ **[{self.selected_char_name}]** の余剰分を1体変換し、**💎 輝石 x1** を獲得しました！\n"
                f"（※本体1体は手元に残っています。残りストック: {target_char['count']}体）",
                ephemeral=True
            )
        else:
            # 万が一、本体しかいない（count == 1）のにリストに出てきてしまった場合のガード
            await interaction.response.send_message(
                "❌ このキャラクターは本体1体のみ所持しているため、変換できません（本体は残す仕様のため）。",
                ephemeral=True
            )
            return

        # 再度、変換可能なキャラリストを更新
        self.max_lb_chars = [
            c for c in u_data.get("characters", [])
            if c.get("limit_break", 0) >= 5 and c.get("count", 1) > 1  # 余剰があるものに限定
        ]
        
        if not self.max_lb_chars:
            await interaction.message.edit(content="✨ 変換できる余剰の完凸キャラクターはいなくなりました。", embed=None, view=None)
        else:
            self.selected_char_name = None
            self.update_select()
            embed = interaction.message.embeds[0]
            await interaction.message.edit(embed=embed, view=self)


class ConvertCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="convert", description="完凸(+5)した重複キャラクターを輝石に変換します")
    async def convert_cmd(self, interaction: discord.Interaction):
        u_data = db.get_user_profile(interaction.user.id)
        user_chars = u_data.get("characters", [])

        # 凸が +5 以上のキャラクターだけを抽出
        max_lb_chars = [c for c in user_chars if c.get("limit_break", 0) >= 5]

        if not max_lb_chars:
            await interaction.response.send_message(
                "❌ 輝石に変換できるキャラクター（凸+5以上の完凸キャラ）がいません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="♻️ キャラクター輝石変換所",
            description=(
                "凸が **+5（完凸）** に達しているキャラクターを選択して、輝石に変換できます。\n\n"
                "👇 下のメニューからキャラクターを選んで「決定」を押してください。"
            ),
            color=0xE67E22
        )

        view = CharacterConvertView(interaction.user.id, max_lb_chars)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConvertCog(bot))
