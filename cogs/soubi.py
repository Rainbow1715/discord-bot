import discord
from discord import app_commands
from discord.ext import commands
from database import get_user_profile, save_data

def get_equip_display(character_data: dict) -> str:
    """キャラの現在装備を取得し、ベスト装備と一致していれば ✨ を付けて返す"""
    current_equip = character_data.get("equip")
    best_equip = character_data.get("best_equip")

    if not current_equip:
        return "なし"

    # 現在の装備とベスト装備が一致している場合は ✨ を先頭に付与
    if best_equip and current_equip == best_equip:
        return f"✨{current_equip}"

    return current_equip

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
        raw_equipments = u_data.get("equipments", [])

        if not characters:
            await interaction.response.send_message("❌ 所持しているキャラクターがいません。", ephemeral=True)
            return

        user_equipments = list(set(
            eq["name"] for eq in raw_equipments 
            if isinstance(eq, dict) and eq.get("name") in EQUIPMENT_MASTER
        ))

        view = EquipSelectView(user_id=interaction.user.id, characters=characters, user_equipments=user_equipments)
        
        embed = discord.Embed(
            title="🗡️ 装備変更",
            description="装備を変更したい **キャラクター** と **装備品** を選択してください。\n（「装備を外す」を選ぶことも可能です）",
            color=0x3498DB
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# --------------------------------------------------
# 🗡️ 装備選択用の Select / View
# --------------------------------------------------
class EquipSelectView(discord.ui.View):
    def __init__(self, user_id: int, characters: list, user_equipments: list):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.selected_char_idx = None
        self.selected_equip = None

        # ① キャラクター選択ドロップダウン（get_equip_display を使用して現在装備を表示）
        char_options = [
            discord.SelectOption(
                label=f"{c.get('name', 'キャラ')} (現在: {get_equip_display(c)})",
                value=str(i)
            ) for i, c in enumerate(characters[:25]) # Selectの上限は25個
        ]
        self.char_select = discord.ui.Select(placeholder="👤 キャラクターを選択", options=char_options, custom_id="select_char")
        self.char_select.callback = self.on_char_select
        self.add_item(self.char_select)

        # ② 装備品選択ドロップダウン
        equip_options = [discord.SelectOption(label="❌ 装備を外す", value="NONE")]
        for eq in user_equipments[:24]:
            equip_options.append(discord.SelectOption(label=f"🗡️ {eq}", value=eq))

        self.equip_select = discord.ui.Select(placeholder="🗡️ 装備品を選択", options=equip_options, custom_id="select_equip")
        self.equip_select.callback = self.on_equip_select
        self.add_item(self.equip_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def on_char_select(self, interaction: discord.Interaction):
        self.selected_char_idx = int(self.char_select.values[0])
        await interaction.response.defer()

    async def on_equip_select(self, interaction: discord.Interaction):
        self.selected_equip = self.equip_select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="決定", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.selected_char_idx is None or self.selected_equip is None:
            await interaction.response.send_message("⚠️ キャラクターと装備品の両方を選択してください！", ephemeral=True)
            return

        u_data = get_user_profile(interaction.user.id)
        target_char = u_data["characters"][self.selected_char_idx]

        # 装備の付け替え処理
        if self.selected_equip == "NONE":
            target_char["equip"] = None
            msg = f"🧹 **{target_char['name']}** の装備を外しました。"
        else:
            target_char["equip"] = self.selected_equip
            # 装備反映後の最新表示（✨含む）を取得
            display_name = get_equip_display(target_char)
            msg = f"⚔️ **{target_char['name']}** に **{display_name}** を装備させました！"

        save_data()
        self.stop()
        
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SoubiCog(bot))
