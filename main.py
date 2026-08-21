import os
import discord
from discord.ext import commands

from database import user_data, get_user_profile, save_data
from gacha import GachaView
from shop import ShopView
from battle import run_battle  # 👈 battle.py から処理を呼び出し
import admin

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await admin.setup(self)  # 👈 管理者コマンドを登録
        await self.tree.sync()
        print("スラッシュコマンドの同期が完了しました！")

bot = MyBot()


class PartySelectView(discord.ui.View):
    def __init__(self, user_id, characters, current_indices):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.characters = characters

        options = []
        for idx, c in enumerate(characters[:25]):
            is_default = idx in current_indices
            count_str = f" (★{c.get('count', 1)}凸)" if c.get('count', 1) > 1 else ""
            options.append(
                discord.SelectOption(
                    label=f"{c['name']}{count_str} (Lv.{c['level']})",
                    value=str(idx),
                    description=f"HP:{c['hp']} / ATK:{c['atk']} / SPD:{c['spd']}",
                    default=is_default,
                )
            )

        max_select = min(3, len(characters))
        select = discord.ui.Select(
            placeholder="出撃させるメンバーを選んでください（最大3体）",
            min_values=1,
            max_values=max_select,
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ あなたのパーティ設定画面ではありません。", ephemeral=True)
            return

        select_item = self.children[0]
        selected_indices = [int(v) for v in select_item.values]

        u_data = get_user_profile(self.user_id)
        u_data["party_indices"] = selected_indices
        save_data()

        names = [self.characters[i]["name"] for i in selected_indices]

        embed = discord.Embed(
            title=f"🛡️ {interaction.user.display_name} の出撃パーティ",
            color=0x1ABC9C,
        )
        msg = ""
        for idx, c_idx in enumerate(selected_indices, start=1):
            c = self.characters[c_idx]
            msg += f"**{idx}. {c['name']}** (Lv.{c['level']} / HP: {c['hp']} / ATK: {c['atk']})\n"

        embed.description = f"{msg}\n✅ **パーティ編成を更新しました！**\n（出撃メンバー: {', '.join(names)}）"
        await interaction.response.edit_message(embed=embed, view=None)


@bot.tree.command(name="profile", description="自分のプロフィールを確認します")
async def profile(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    char_count = len(u_data["characters"])

    def get_total_power(data):
        return sum(c["level"] * 10 + c["atk"] + c["hp"] for c in data["characters"])

    all_users = list(user_data.items())

    sorted_by_power = sorted(all_users, key=lambda x: get_total_power(x[1]), reverse=True)
    power_rank = [i for i, u in enumerate(sorted_by_power) if u[0] == interaction.user.id][0] + 1

    sorted_by_chars = sorted(all_users, key=lambda x: len(x[1]["characters"]), reverse=True)
    char_rank = [i for i, u in enumerate(sorted_by_chars) if u[0] == interaction.user.id][0] + 1

    embed = discord.Embed(title=f"👤 {interaction.user.display_name} のプロフィール", color=0x3498DB)
    embed.add_field(name="💰 所持金", value=f"{u_data['gold']} G", inline=True)
    embed.add_field(name="👥 所持キャラ種類", value=f"{char_count} 種", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="🏆 強さ順位", value=f"{power_rank} 位 / {len(all_users)} 人中", inline=True)
    embed.add_field(name="📦 キャラ所持種類順位", value=f"{char_rank} 位 / {len(all_users)} 人中", inline=True)

    await interaction.response.send_message(embed=embed)

# --------------------------------------------------
# 🎨 表示用アイコン（絵文字）の定義
# --------------------------------------------------
ELEMENT_ICONS = {
    "赤": "❤️",
    "緑": "💚",
    "青": "💙",
    "光": "💛",
    "紫": "💜"
}

ROLE_ICONS = {
    "アタッカー": "⚔️",
    "サポーター": "🤝",
    "ディフェンダー": "🛡️"
}


@bot.tree.command(name="chars", description="所持キャラクターの一覧とステータスを確認します")
async def chars(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)

    embed = discord.Embed(
        title=f"⚔️ {interaction.user.display_name} の所持キャラ一覧 (全 {len(u_data['characters'])} 種)",
        color=0x9B59B6,
    )

    for idx, c in enumerate(u_data["characters"], start=1):
        next_exp = c["level"] * 100
        rarity_str = f" [{c.get('rarity', '★3')}]"
        count_str = f" (所持数: {c.get('count', 1)})" if c.get('count', 1) > 1 else ""

        # 各項目の取得
        elem_str = c.get("element", "なし")
        role_str = c.get("role", "アタッカー")
        gender_str = c.get("gender", "？")

        elem_icon = ELEMENT_ICONS.get(elem_str, "🎨")
        role_icon = ROLE_ICONS.get(role_str, "🛡️")

        # 🎭 キャラ固有の顔文字アイコン（データになければ属性アイコンで代用）
        char_icon = c.get("icon") if c.get("icon") else elem_icon

        # 装備ボーナス表示の判定
        equip_name = c.get('equip') or 'なし'
        is_best = c.get('equip') and c.get('equip') == c.get('best_equip')
        equip_bonus_str = " ✨(ATK+20%!)" if is_best else ""

        # メッセージ作成
        status_msg = (
            f"**Lv.{c['level']}**{count_str} (XP: {c['exp']} / {next_exp})\n"
            f"{elem_icon} **属性**: {elem_str} | {role_icon} **ロール**: {role_str} | **性別**: {gender_str}\n"
            f"🗡️ **装備**: {equip_name}{equip_bonus_str}\n"
            f"❤️ **HP**: {c['hp']} | 🗡️ **攻撃力**: {c['atk']}\n"
            f"⚡ **速度**: {c['spd']} | 💖 **回復量**: {c['rec']}\n"
            f"✨ **スキル**: {c['skill_name']} (威力: {c['skill_pow']})"
        )
        # タイトルにレオたちの顔文字を表示！
        embed.add_field(name=f"[{idx}] {char_icon} {c['name']}{rarity_str}", value=status_msg, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="party", description="出撃パーティの確認と編成変更を行います")
async def party(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)

    embed = discord.Embed(title=f"🛡️ {interaction.user.display_name} の出撃パーティ", color=0x1ABC9C)

    party_members = [u_data["characters"][i] for i in u_data["party_indices"] if i < len(u_data["characters"])]

    msg = ""
    for idx, c in enumerate(party_members, start=1):
        msg += f"**{idx}. {c['name']}** (Lv.{c['level']} / HP: {c['hp']} / ATK: {c['atk']})\n"

    embed.description = msg + "\n👇 下のメニューから出撃させたいメンバーを選択してください（最大3体）。"

    view = PartySelectView(interaction.user.id, u_data["characters"], u_data["party_indices"])
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="battle", description="敵とオートバトルを行います")
async def battle(interaction: discord.Interaction):
    await run_battle(interaction)


@bot.tree.command(name="gacha", description="虹の欠片やチケットを使って10連ガチャを回します")
async def gacha(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    items = u_data["items"]

    rainbow_count = items.get("虹の欠片", 0)
    ticket_count = items.get("ガチャチケ", 0)

    embed = discord.Embed(
        title="🎰 キャラクター召喚（10連ガチャ）",
        description=(
            f"10連ガチャを回して新しい仲間を獲得できます！\n\n"
            f"💎 **所持 虹の欠片**: {rainbow_count} 個 (必要: 1000個)\n"
            f"🎫 **所持 ガチャチケ**: {ticket_count} 枚 (必要: 10枚)\n\n"
            f"👇 下のボタンを押してガチャを回してください。"
        ),
        color=0x9B59B6,
    )

    view = GachaView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="shop", description="ゴールドを使ってアイテムやガチャ箱を購入します")
async def shop(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)

    embed = discord.Embed(
        title="🏪 アイテムショップ",
        description=(
            f"💰 **所持金**: {u_data['gold']} G\n\n"
            f"📦 **ランダムガチャチケ箱**: 1000 G\n"
            f"└ 開封すると **1〜10枚** のガチャチケが出現！\n"
            f"└ 確率1%で **超大当たり 100枚**！！"
        ),
        color=0xF1C40F
    )
    view = ShopView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="mailbox", description="届いているメールや報酬を確認・受け取ります")
async def mailbox(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    mails = u_data.get("mails", [])

    unclaimed_mails = [m for m in mails if not m.get("claimed", False)]

    if not unclaimed_mails:
        await interaction.response.send_message("📬 未受け取りのメールはありません。", ephemeral=True)
        return

    # 未受取メールの報酬をまとめて獲得
    total_gold = 0
    total_rainbow = 0
    total_ticket = 0
    mail_titles = []

    for m in unclaimed_mails:
        total_gold += m.get("gold", 0)
        total_rainbow += m.get("rainbow", 0)
        total_ticket += m.get("ticket", 0)
        m["claimed"] = True
        mail_titles.append(m["title"])

    u_data["gold"] += total_gold
    u_data["items"]["虹の欠片"] = u_data["items"].get("虹の欠片", 0) + total_rainbow
    u_data["items"]["ガチャチケ"] = u_data["items"].get("ガチャチケ", 0) + total_ticket
    save_data()

    embed = discord.Embed(
        title="🎁 メール報酬を受け取りました！",
        description="\n".join([f"・{t}" for t in mail_titles]),
        color=0x2ECC71
    )
    embed.add_field(name="獲得アイテム", value=(
        f"💰 **ゴールド**: +{total_gold} G\n"
        f"💎 **虹の欠片**: +{total_rainbow} 個\n"
        f"🎫 **ガチャチケ**: +{total_ticket} 枚"
    ))

    await interaction.response.send_message(embed=embed, ephemeral=True)

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
