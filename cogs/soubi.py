import discord
from discord import app_commands
from discord.ext import commands
import database as db
from database import get_user_profile, save_data, _normalize_equipments


def get_equip_display(character_data: dict) -> str:
    """キャラの現在装備を取得し、ベスト装備と一致していれば ✨ を付けて返す"""
    current_equip = character_data.get("equip")
    best_equip = character_data.get("best_equip")

    if not current_equip:
        return "なし"

    # best_equip がリスト（複数）の場合と文字列（単体）の場合の両方に対応して判定
    is_best = False
    if isinstance(best_equip, list):
        if current_equip in best_equip:
            is_best = True
    elif isinstance(best_equip, str):
        if current_equip == best_equip:
            is_best = True

    # 一致している場合は ✨ を先頭に付与
    if is_best:
        return f"✨{current_equip}"

    return current_equip

# ⚔️ 装備のピックアップ設定
NEW_PICKUP_EQUIPMENTS = ["クソデカ十字架", "Branchの上着"]    # 新しく実装された装備
BIRTHDAY_PICKUP_EQUIPMENTS = ["ハリセン"] # 誕生月などのピックアップ装備
EQUIP_PICKUP_BOOST_RATE = 0.50              # ピックアップ全体の補正率
EQUIP_BIRTHDAY_PICKUP_BOOST_RATE = 0.60     # 誕生月ピックアップ全体の補正率

# 🗡️ 装備マスタデータ
EQUIPMENT_MASTER = {
    "鉄の剣": {"icon": "⚔️", "rarity": 3, "atk": 10, "description": "一般的な鉄製の剣。"},
    "鋼の剣": {"icon": "⚔️", "rarity": 4, "atk": 25, "description": "鍛え抜かれた鋼の剣。"},
    "聖剣エクスカリバー": {"icon": "🗡️", "rarity": 5, "atk": 60, "description": "伝説の聖剣。"},
    "なんか強そうな棒": {"icon": "", "rarity": 3, "atk": 10, "description": "その辺に落ちてそうな棒。強いのか？"},
    "紙パックのいちごオレ": {"icon": "", "rarity": 4, "p_hp": 100, "description": "美味しい。毎ターンHP100回復。"},
    "ナイフ": {"icon": "", "rarity": 3, "atk": 50, "description": "普通のナイフ。"},
    "ロケット": {"icon": "", "rarity": 3, "atk": 10, "description": "中に女性の写真が入っている。"},
    "電子機器": {"icon": "", "rarity": 5, "atk": 500, "description": "ばか"},
    "子供用カメラ": {"icon": "", "rarity": 3, "atk": 10, "description": "一応撮れる。"},
    "ハリセン": {"icon": "", "rarity": 3, "atk": 35, "description": "いい音が鳴りそう。"},
    "学校の箒": {"icon": "", "rarity": 3, "atk": 10, "description": "掃除でもするんですか？"},
    "鏡": {"icon": "", "rarity": 3, "atk": 10, "description": "この世で1番美しいのはだぁれ？"},
    "怪しい試験管": {"icon": "", "rarity": 3, "p_hp": 70, "description": "何が入ってるんですかこれ"},
    "酒瓶": {"icon": "", "rarity": 3, "atk": 50, "description": "割れると痛いですよ。"},
    "片手剣": {"icon": "", "rarity": 3, "atk": 50, "description": "なんか不思議な力で作られている、黄色い剣。"},
    "苦いクッキー": {"icon": "", "rarity": 3, "p_hp": 60, "description": "ともだちとお外を眺めてた"},
    "ビートクローザー": {"icon": "", "rarity": 4, "atk": 60, "description": "なんかかっこいいけん"},
    "思い出の写真": {"icon": "", "rarity": 4, "p_hp": 82, "description": "黒髪の男性が写っている"},
    "ビリーザロッド": {"icon": "", "rarity": 4, "stun": 95, "description": "これでビリビリにします"},
    "大きなハサミ": {"icon": "", "rarity": 4, "atk": 60, "description": "このハサミで切られても血は出ない"},
    "狐柄の毛布": {"icon": "", "rarity": 4, "def": 0.20, "description": "何回も洗濯したから少しボロボロ"},
    "牛のぬいぐるみ": {"icon": "", "rarity": 4, "atk": 0.20, "description": "ボコボコにする？"},
    "カボチャのバケツ": {"icon": "", "rarity": 4, "p_hp": 120, "description": "バケツいっぱいにお菓子をもらったら、きっと幸せだね"},
    "クソデカ十字架": {"icon": "", "rarity": 3, "atk": 0.60, "description": "ぶん回す"},
    "Branchの上着": {"icon": "", "rarity": 3, "p_hp": 84, "description": "え？ お前それ盗って行ったの？ ないわー"},
}


class SoubiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. 装備ガチャコマンド
    @commands.command(name="装備ガチャ")
    async def open_soubi_gacha(self, ctx):
        from gacha import SoubiGachaView
        view = SoubiGachaView(ctx.author.id)
        await ctx.send("🗡️ 装備ガチャ", view=view)

    # 2. 装備装着スラッシュコマンド (/equip)
    @app_commands.command(name="equip", description="所持キャラクターに装備を装着・変更します")
    async def equip(self, interaction: discord.Interaction):
        u_data = get_user_profile(interaction.user.id)
        characters = u_data.get("characters", [])
        
        if not characters:
            await interaction.response.send_message("❌ 所持しているキャラクターがいません。", ephemeral=True)
            return

        # 🔄 辞書型（または旧形式）の所持装備を正規化して、1個以上持っている装備名のリストを作る
        raw_equipments = u_data.get("equipments", {})
        equip_dict = _normalize_equipments(raw_equipments)
        
        user_equipments = [
            eq_name for eq_name, count in equip_dict.items() 
            if count > 0 and eq_name in EQUIPMENT_MASTER
        ]

        view = EquipSelectView(user_id=interaction.user.id, characters=characters, user_equipments=user_equipments)
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# --------------------------------------------------
# 🗡️ 装備選択用の ページ送り対応 View
# --------------------------------------------------
class EquipSelectView(discord.ui.View):
    def __init__(self, user_id: int, characters: list, user_equipments: list):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.characters = characters
        self.user_equipments = user_equipments

        self.char_page = 0
        self.equip_page = 0

        self.selected_char_idx = None
        self.selected_equip = None

        self.update_components()

    def update_components(self):
        self.clear_items()

        # --- ① キャラクター選択用セレクト（最大25件表示） ---
        char_start = self.char_page * 25
        char_end = char_start + 25
        current_chars = list(enumerate(self.characters))[char_start:char_end]

        char_options = [
            discord.SelectOption(
                label=f"{c.get('name', 'キャラ')} (現在: {get_equip_display(c)})",
                value=str(i),
                default=(self.selected_char_idx == i)
            ) for i, c in current_chars
        ]
        if not char_options:
            char_options.append(discord.SelectOption(label="キャラクターなし", value="NONE"))

        self.char_select = discord.ui.Select(
            placeholder=f"👤 キャラ選択 (ページ {self.char_page + 1})",
            options=char_options,
            custom_id="select_char",
            row=0
        )
        self.char_select.callback = self.on_char_select
        self.add_item(self.char_select)

        # --- キャラクターページ送りボタン（25件以上いる場合のみ） ---
        if len(self.characters) > 25:
            max_char_page = (len(self.characters) - 1) // 25
            prev_char_btn = discord.ui.Button(label="◀ キャラ前へ", style=discord.ButtonStyle.secondary, disabled=(self.char_page == 0), row=1)
            next_char_btn = discord.ui.Button(label="キャラ次へ ▶", style=discord.ButtonStyle.secondary, disabled=(self.char_page >= max_char_page), row=1)

            async def prev_char_cb(interaction: discord.Interaction):
                if interaction.user.id != self.user_id:
                    return await interaction.response.send_message("❌ 他人の操作です。", ephemeral=True)
                self.char_page -= 1
                self.update_components()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)

            async def next_char_cb(interaction: discord.Interaction):
                if interaction.user.id != self.user_id:
                    return await interaction.response.send_message("❌ 他人の操作です。", ephemeral=True)
                self.char_page += 1
                self.update_components()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)

            prev_char_btn.callback = prev_char_cb
            next_char_btn.callback = next_char_cb
            self.add_item(prev_char_btn)
            self.add_item(next_char_btn)

        # --- ② 装備品選択用セレクト（最大24件 + 外す） ---
        equip_start = self.equip_page * 24
        equip_end = equip_start + 24
        current_equips = self.user_equipments[equip_start:equip_end]

        equip_options = [
            discord.SelectOption(
                label="❌ 装備を外す",
                value="NONE",
                default=(self.selected_equip == "NONE")
            )
        ]
        for eq in current_equips:
            equip_options.append(
                discord.SelectOption(
                    label=f"🗡️ {eq}",
                    value=eq,
                    default=(self.selected_equip == eq)
                )
            )

        self.equip_select = discord.ui.Select(
            placeholder=f"🗡️ 装備選択 (ページ {self.equip_page + 1})",
            options=equip_options,
            custom_id="select_equip",
            row=2
        )
        self.equip_select.callback = self.on_equip_select
        self.add_item(self.equip_select)

        # --- 装備ページ送りボタン（24件以上ある場合のみ） ---
        if len(self.user_equipments) > 24:
            max_equip_page = (len(self.user_equipments) - 1) // 24
            prev_equip_btn = discord.ui.Button(label="◀ 装備前へ", style=discord.ButtonStyle.secondary, disabled=(self.equip_page == 0), row=3)
            next_equip_btn = discord.ui.Button(label="装備次へ ▶", style=discord.ButtonStyle.secondary, disabled=(self.equip_page >= max_equip_page), row=3)

            async def prev_equip_cb(interaction: discord.Interaction):
                if interaction.user.id != self.user_id:
                    return await interaction.response.send_message("❌ 他人の操作です。", ephemeral=True)
                self.equip_page -= 1
                self.update_components()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)

            async def next_equip_cb(interaction: discord.Interaction):
                if interaction.user.id != self.user_id:
                    return await interaction.response.send_message("❌ 他人の操作です。", ephemeral=True)
                self.equip_page += 1
                self.update_components()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)

            prev_equip_btn.callback = prev_equip_cb
            next_equip_btn.callback = next_equip_cb
            self.add_item(prev_equip_btn)
            self.add_item(next_equip_btn)

        # --- ③ 決定ボタン ---
        confirm_btn = discord.ui.Button(label="決定", style=discord.ButtonStyle.success, row=4)
        confirm_btn.callback = self.confirm
        self.add_item(confirm_btn)

    def create_embed(self) -> discord.Embed:
        selected_char_name = "未選択"
        if self.selected_char_idx is not None and self.selected_char_idx < len(self.characters):
            selected_char_name = self.characters[self.selected_char_idx].get("name", "不明")

        selected_eq_name = "未選択"
        if self.selected_equip == "NONE":
            selected_eq_name = "装備を外す"
        elif self.selected_equip is not None:
            selected_eq_name = self.selected_equip

        embed = discord.Embed(
            title="🗡️ 装備変更",
            description=(
                "装備を変更したい **キャラクター** と **装備品** を選択してください。\n"
                "（25体以上いる場合は下のボタンでページを切り替えられます）\n\n"
                f"👤 **選択中キャラ**: **{selected_char_name}**\n"
                f"🗡️ **選択中装備**: **{selected_eq_name}**"
            ),
            color=0x3498DB
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def on_char_select(self, interaction: discord.Interaction):
        self.selected_char_idx = int(self.char_select.values[0])
        self.update_components()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_equip_select(self, interaction: discord.Interaction):
        self.selected_equip = self.equip_select.values[0]
        self.update_components()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def confirm(self, interaction: discord.Interaction):  # 👈 button 引数を削除！
        if self.selected_char_idx is None or self.selected_equip is None:
            await interaction.response.send_message("⚠️ キャラクターと装備品の両方を選択してください！", ephemeral=True)
            return

        u_data = get_user_profile(interaction.user.id)
        target_char = u_data["characters"][self.selected_char_idx]

        # 装備を外す場合
        if self.selected_equip == "NONE":
            target_char["equip"] = None
            msg = f"🧹 **{target_char['name']}** の装備を外しました。"
        else:
            # 🛡️ ストック数（余り）のチェック処理
            equip_dict = _normalize_equipments(u_data.get("equipments", {}))
            owned_count = equip_dict.get(self.selected_equip, 0)

            # 既に他のキャラクターがこの装備をつけている数をカウントする
            equipped_count = sum(
                1 for i, c in enumerate(u_data.get("characters", []))
                if i != self.selected_char_idx and c.get("equip") == self.selected_equip
            )

            available_stock = owned_count - equipped_count

            if available_stock <= 0:
                await interaction.response.send_message(
                    f"❌ **{self.selected_equip}** のストックがありません！\n（所持数: {owned_count}個 / 他のキャラクターが装備中です）",
                    ephemeral=True
                )
                return

            # 装備を適用
            target_char["equip"] = self.selected_equip
            display_name = get_equip_display(target_char)
            msg = f"⚔️ **{target_char['name']}** に **{display_name}** を装備させました！"

        save_data()
        self.stop()
        
        await interaction.response.send_message(msg, ephemeral=True)

        # 🔻 🏆 キャラ別の適正装備装着の実績チェック 🔻
        if self.selected_equip != "NONE":
            try:
                from achievement import check_equip_best_achievement
                await check_equip_best_achievement(interaction, target_char, self.selected_equip)
            except Exception as e:
                print(f"実績判定エラー: {e}")


async def setup(bot):
    await bot.add_cog(SoubiCog(bot))
