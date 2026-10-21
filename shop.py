import random
import discord
from discord import app_commands
from discord.ext import commands
import database as db


class ShopView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.selected_char_name = None
        self.char_page = 0
        self.per_page = 20  # 1ページあたり20体表示

        self.update_char_select()

    def update_char_select(self):
        """キャラクター選択ドロップダウンとページ切替ボタンを動的に更新"""
        # 既存の動的アイテム（ドロップダウン・ページボタン）を削除
        for item in list(self.children):
            if getattr(item, "is_dynamic_char_item", False):
                self.remove_item(item)

        total_chars = len(db.GACHA_POOL)
        max_page = max(0, (total_chars - 1) // self.per_page)
        
        start_idx = self.char_page * self.per_page
        end_idx = start_idx + self.per_page
        page_chars = db.GACHA_POOL[start_idx:end_idx]

        options = []
        for c in page_chars:
            c_name = c.get("name")
            rarity = c.get("rarity", "★3")
            options.append(discord.SelectOption(label=f"[{rarity}] {c_name}", value=c_name))

        if not options:
            options.append(discord.SelectOption(label="キャラがいません", value="NONE"))

        # ドロップダウン作成
        char_select = discord.ui.Select(
            placeholder=f"👤 キャラを選択 (ページ {self.char_page + 1}/{max_page + 1})",
            options=options,
            custom_id="select_shop_char",
            row=2
        )
        char_select.is_dynamic_char_item = True
        char_select.callback = self.on_char_select
        self.add_item(char_select)

        # ◀ 前ページボタン
        prev_btn = discord.ui.Button(
            label="◀ 前のキャラ",
            style=discord.ButtonStyle.secondary,
            disabled=(self.char_page == 0),
            row=3
        )
        prev_btn.is_dynamic_char_item = True
        prev_btn.callback = self.prev_char_page
        self.add_item(prev_btn)

        # 次ページ ▶ ボタン
        next_btn = discord.ui.Button(
            label="次のキャラ ▶",
            style=discord.ButtonStyle.secondary,
            disabled=(self.char_page >= max_page),
            row=3
        )
        next_btn.is_dynamic_char_item = True
        next_btn.callback = self.next_char_page
        self.add_item(next_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他のユーザーのショップ画面です。", ephemeral=True)
            return False
        return True

    async def on_char_select(self, interaction: discord.Interaction):
        if self.children:
            # 選択された値を取得
            for child in self.children:
                if isinstance(child, discord.ui.Select) and child.custom_id == "select_shop_char":
                    if child.values and child.values[0] != "NONE":
                        self.selected_char_name = child.values[0]
        await interaction.response.defer()

    async def prev_char_page(self, interaction: discord.Interaction):
        if self.char_page > 0:
            self.char_page -= 1
            self.update_char_select()
            await interaction.response.edit_message(view=self)

    async def next_char_page(self, interaction: discord.Interaction):
        max_page = (len(db.GACHA_POOL) - 1) // self.per_page
        if self.char_page < max_page:
            self.char_page += 1
            self.update_char_select()
            await interaction.response.edit_message(view=self)

    # 📦 ガチャチケ箱（1000G）
    @discord.ui.button(label="ランダムガチャチケ箱 (1000 G)", style=discord.ButtonStyle.success, emoji="📦", row=0)
    async def buy_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        u_data = db.get_user_profile(self.user_id)
        if u_data["gold"] < 1000:
            await interaction.response.send_message("❌ ゴールドが足りません！（必要: 1000 G）", ephemeral=True)
            return

        u_data["gold"] -= 1000
        is_jackpot = random.randint(1, 100) == 1
        tickets = 100 if is_jackpot else random.randint(1, 10)
        
        items = u_data["items"]
        items["ガチャチケ"] = items.get("ガチャチケ", 0) + tickets
        db.save_data()

        msg = "🎉🎉 **超大当たり！！** ガチャチケ **100枚** を獲得！ 🎉🎉" if is_jackpot else f"📦 ガチャチケ **{tickets}枚** を獲得しました！"
        embed = discord.Embed(
            title="🛍️ 購入完了！",
            description=f"{msg}\n\n💰 所持金: {u_data['gold']:,} G | 🎫 所持チケット: {items['ガチャチケ']} 枚",
            color=0xFFD700 if is_jackpot else 0x2ECC71,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 🛡️ 装備ガチャチケ箱（1000G）
    @discord.ui.button(label="装備ガチャチケ箱 (1000 G)", style=discord.ButtonStyle.secondary, emoji="🛡️", row=0)
    async def buy_equip_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        u_data = db.get_user_profile(self.user_id)
        if u_data["gold"] < 1000:
            await interaction.response.send_message("❌ ゴールドが足りません！（必要: 1000 G）", ephemeral=True)
            return

        u_data["gold"] -= 1000
        is_jackpot = random.randint(1, 100) == 1
        tickets = 100 if is_jackpot else random.randint(1, 10)

        items = u_data["items"]
        items["装備ガチャチケ"] = items.get("装備ガチャチケ", 0) + tickets
        db.save_data()

        msg = "🎉🎉 **超大当たり！！** 装備ガチャチケ **100枚** を獲得！ 🎉🎉" if is_jackpot else f"🛡️ 装備ガチャチケ **{tickets}枚** を獲得しました！"
        embed = discord.Embed(
            title="🛍️ 購入完了！",
            description=f"{msg}\n\n💰 所持金: {u_data['gold']:,} G | 🛡️ 所持チケット: {items['装備ガチャチケ']} 枚",
            color=0xFFD700 if is_jackpot else 0x2ECC71,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 🎁 ランダムご飯ボックス（800G）
    @discord.ui.button(label="ランダムご飯ボックス (800 G)", style=discord.ButtonStyle.primary, emoji="🎁", row=1)
    async def buy_food_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_info = db.get_user_profile(self.user_id)
        if user_info["gold"] < 800:
            await interaction.response.send_message("❌ ゴールドが足りません！（必要: 800 G）", ephemeral=True)
            return

        user_info["gold"] -= 800
        all_food_names = list(db.FOOD_ITEMS.keys())
        gained_foods = {}

        for _ in range(10):
            chosen = random.choice(all_food_names)
            gained_foods[chosen] = gained_foods.get(chosen, 0) + 1
            user_info["items"][chosen] = user_info["items"].get(chosen, 0) + 1

        db.save_data()

        result_lines = [f"・{db.FOOD_ITEMS[fn].get('icon', '🍱')} **{fn}** x{cnt}" for fn, cnt in gained_foods.items()]
        embed = discord.Embed(
            title="🎁 ランダムご飯ボックスを開封した！",
            description="合計10個のご飯を手に入れたよ！\n\n" + "\n".join(result_lines),
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"残高: {user_info['gold']:,} G")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 💎 輝石20個 ➔ かけら1個
    @discord.ui.button(label="輝石20個 ➔ かけら1個", style=discord.ButtonStyle.primary, emoji="💎", row=4)
    async def buy_piece(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_char_name:
            await interaction.response.send_message("⚠️ 下のドロップダウンから対象のキャラクターを選択してください！", ephemeral=True)
            return

        u_data = db.get_user_profile(self.user_id)
        items = u_data.setdefault("items", {})
        kiseki_count = items.get("輝石", 0)

        if kiseki_count < 20:
            await interaction.response.send_message(f"❌ 輝石が足りません！（所持: {kiseki_count}個 / 必要: 20個）", ephemeral=True)
            return

        items["輝石"] -= 20
        piece_name = f"{self.selected_char_name}のかけら"
        items[piece_name] = items.get(piece_name, 0) + 1

        db.save_data()

        await interaction.response.send_message(
            f"✨ **輝石 20個** を消費して **[{piece_name}]** を1個獲得しました！\n"
            f"（現在の所持数: {items[piece_name]} / 20個）",
            ephemeral=True,
        )

    # 🧩 かけら20個 ➔ キャラ解放（召喚）
    @discord.ui.button(label="かけら20個 ➔ キャラ解放", style=discord.ButtonStyle.success, emoji="🧩", row=4)
    async def exchange_character(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_char_name:
            await interaction.response.send_message("⚠️ 下のドロップダウンから対象のキャラクターを選択してください！", ephemeral=True)
            return

        u_data = db.get_user_profile(self.user_id)
        items = u_data.setdefault("items", {})
        piece_name = f"{self.selected_char_name}のかけら"
        piece_count = items.get(piece_name, 0)

        if piece_count < 20:
            await interaction.response.send_message(f"❌ かけらが足りません！（所持: {piece_count}個 / 必要: 20個）", ephemeral=True)
            return

        items[piece_name] -= 20
        user_chars = u_data.setdefault("characters", [])
        existing_char = next((c for c in user_chars if c["name"] == self.selected_char_name), None)

        if existing_char:
            # すでに所持している場合は限界突破（+1）または所持数を増加
            existing_char["limit_break"] = existing_char.get("limit_break", 0) + 1
            msg = f"🎉 **[{self.selected_char_name}]** を獲得し、限界突破数が **+{existing_char['limit_break']}** になりました！"
        else:
            template = db.find_gacha_char(self.selected_char_name)
            if template:
                new_char = {
                    "name": template["name"],
                    "rarity": template.get("rarity", "★3"),
                    "icon": template.get("icon"),
                    "count": 1,
                    "limit_break": 0,
                    "level": 1,
                    "exp": 0,
                    "max_hp": template.get("max_hp", template.get("hp", 100)),
                    "hp": template.get("hp", 100),
                    "atk": template.get("atk", 10),
                    "spd": template.get("spd", 10),
                    "rec": template.get("rec", 10),
                    "skill_name": template.get("skill_name", "通常攻撃"),
                    "skill_pow": template.get("skill_pow", 1.0),
                }
                user_chars.append(new_char)
                msg = f"✨NEW!✨ **[{self.selected_char_name}]** を仲間として迎えました！"
            else:
                msg = "❌ キャラクターデータの取得に失敗しました。"

        db.save_data()
        await interaction.response.send_message(msg, ephemeral=True)


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="ショップでアイテムを購入・交換します")
    async def shop_cmd(self, interaction: discord.Interaction):
        u_data = db.get_user_profile(interaction.user.id)
        items = u_data.get("items", {})

        embed = discord.Embed(
            title="🛍️ よろず屋 ＆ かけら交換所",
            description=(
                f"💰 **所持金**: {u_data.get('gold', 0):,} G | 💎 **所持 輝石**: {items.get('輝石', 0)} 個\n"
                "───────────────────\n"
                "**【お買い物】**\n"
                "・📦 ガチャチケ箱 (1000G)\n"
                "・🛡️ 装備ガチャチケ箱 (1000G)\n"
                "・🎁 ランダムご飯ボックス (800G)\n\n"
                "**【かけら交換所】**\n"
                "・💎 輝石 20個 ➔ 選択キャラの「かけら 1個」\n"
                "・🧩 キャラのかけら 20個 ➔ そのキャラを獲得！\n"
                "*(※ 下のドロップダウン・ページ切り替えでキャラを選んでね)*"
            ),
            color=0x9B59B6,
        )

        view = ShopView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ShopCog(bot))
