import copy
import os

import admin
from aiohttp import web
from database import GACHA_POOL, get_user_profile, save_data, user_data
from gacha import GachaView
from shop import ShopView

import discord
from discord.ext import commands


# --------------------------------------------------
# 🌐 Renderポートエラー回避用のダミーWebサーバー設定
# --------------------------------------------------
async def handle(request):
    return web.Response(text="Bot is running!")


async def start_dummy_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"ダミーWebサーバーがポート {port} で起動しました。")


# --------------------------------------------------
# 🤖 Discord Bot の設定
# --------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True


class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await start_dummy_server()  # 👈 Bot起動時にダミーWebサーバーも一緒に立ち上げる
        await admin.setup(self)  # 👈 管理者コマンドを登録

        # 🔻 Cogの読み込み一覧 🔻
        cogs = [
            "cogs.feed",
            "cogs.item",
            "cogs.rankup",
            "zukan",
            "cogs.reactions",
            "battle",
            "cogs.use",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ {cog} の読み込みに成功しました！")
            except Exception as e:
                print(f"❌ {cog} の読み込みエラー: {e}")

        await self.tree.sync()
        print("スラッシュコマンドの同期が完了しました！")


bot = MyBot()


class PartySelectView(discord.ui.View):

    def __init__(self, user_id, characters, current_indices):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.characters = characters

        options = []
        valid_current_indices = [
            idx for idx in current_indices if idx < len(characters)
        ]

        for idx, c in enumerate(characters[:25]):
            is_default = idx in valid_current_indices

            # レア度の数値（"★3" などの文字列や 3 などの数値に対応）
            raw_rarity = c.get("rarity", 1)
            if isinstance(raw_rarity, str):
                base_rarity = int(raw_rarity.replace("★", "")) if raw_rarity.replace("★", "").isdigit() else 1
            else:
                base_rarity = int(raw_rarity)

            # ⭕️ limit_break をそのまま取得（所持数からの自動計算を完全排除）
            limit_break = c.get("limit_break", 0)
            star_str = f"★{base_rarity} +{limit_break}" if limit_break > 0 else f"★{base_rarity}"

            options.append(
                discord.SelectOption(
                    label=f"{c['name']} ({star_str} / Lv.{c['level']})",
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
            await interaction.response.send_message(
                "❌ あなたのパーティ設定画面ではありません。", ephemeral=True
            )
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
            
            # パーティ設定完了後の表示用レア度計算
            raw_rarity = c.get("rarity", 1)
            if isinstance(raw_rarity, str):
                base_rarity = int(raw_rarity.replace("★", "")) if raw_rarity.replace("★", "").isdigit() else 1
            else:
                base_rarity = int(raw_rarity)
            
            # ⭕️ limit_break をそのまま取得
            limit_break = c.get("limit_break", 0)
            star_str = f"★{base_rarity} +{limit_break}" if limit_break > 0 else f"★{base_rarity}"

            msg += f"**{idx}. {c['name']}** [{star_str}] (Lv.{c['level']} / HP: {c['hp']} / ATK: {c['atk']})\n"

        embed.description = (
            f"{msg}\n✅ **パーティ編成を更新しました！**\n（出撃メンバー:"
            f" {', '.join(names)}）"
        )
        await interaction.response.edit_message(embed=embed, view=None)


@bot.tree.command(name="profile", description="自分のプロフィールを確認します")
async def profile(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    characters = u_data.get("characters", [])
    char_count = len(characters)

    # ⭕️ 安全に総合力を計算する関数
    def get_total_power(data):
        chars = data.get("characters", [])
        return sum(
            c.get("level", 1) * 10 + c.get("atk", 0) + c.get("hp", 0) for c in chars
        )

    all_users = list(user_data.items())

    # 強さ順位の計算
    sorted_by_power = sorted(
        all_users, key=lambda x: get_total_power(x[1]), reverse=True
    )
    power_rank = (
        [i for i, u in enumerate(sorted_by_power) if u[0] == interaction.user.id][0]
        + 1
    )

    # 所持キャラ数順位の計算（⭕️ .get("characters", []) で安全に取得）
    sorted_by_chars = sorted(
        all_users, key=lambda x: len(x[1].get("characters", [])), reverse=True
    )
    char_rank = (
        [i for i, u in enumerate(sorted_by_chars) if u[0] == interaction.user.id][0]
        + 1
    )

    embed = discord.Embed(
        title=f"👤 {interaction.user.display_name} のプロフィール",
        color=0x3498DB,
    )
    embed.add_field(name="💰 所持金", value=f"{u_data.get('gold', 0)} G", inline=True)
    embed.add_field(
        name="👥 所持キャラ種類", value=f"{char_count} 種", inline=True
    )
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(
        name="🏆 強さ順位",
        value=f"{power_rank} 位 / {len(all_users)} 人中",
        inline=True,
    )
    embed.add_field(
        name="📦 キャラ所持種類順位",
        value=f"{char_rank} 位 / {len(all_users)} 人中",
        inline=True,
    )

    await interaction.response.send_message(embed=embed)


# --------------------------------------------------
# 🎨 表示用アイコン（絵文字）の定義
# --------------------------------------------------
ELEMENT_ICONS = {
    "赤": "❤️",
    "緑": "💚",
    "青": "💙",
    "光": "💛",
    "紫": "💜",
}

ROLE_ICONS = {
    "アタッカー": "⚔️",
    "サポーター": "🤝",
    "ディフェンダー": "🛡️",
}


# --------------------------------------------------
# 📖 ステータス画面用 ページネーション View
# --------------------------------------------------
class StatusPaginationView(discord.ui.View):

    def __init__(
        self,
        user_id: int,
        user_display_name: str,
        characters: list,
        per_page: int = 4,
    ):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.user_display_name = user_display_name
        self.characters = characters
        self.per_page = per_page
        self.current_page = 0
        self.max_page = max(0, (len(characters) - 1) // per_page)

        self.update_buttons()

    def update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "prev_page":
                    child.disabled = self.current_page == 0
                elif child.custom_id == "next_page":
                    child.disabled = self.current_page >= self.max_page

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=(
                f"⚔️ {self.user_display_name} の所持キャラ一覧 (全"
                f" {len(self.characters)} 種)"
            ),
            color=0x9B59B6,
        )
        embed.set_footer(
            text=f"ページ {self.current_page + 1} / {self.max_page + 1}"
        )

        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_chars = self.characters[start_idx:end_idx]

        for i, c in enumerate(page_chars, start=start_idx + 1):
            next_exp = c["level"] * 100
            
            # レア度と凸数の計算
            raw_rarity = c.get("rarity", 1)
            if isinstance(raw_rarity, str):
                base_rarity = int(raw_rarity.replace("★", "")) if raw_rarity.replace("★", "").isdigit() else 1
            else:
                base_rarity = int(raw_rarity)

            # ⭕️ limit_break をそのまま取得
            limit_break = c.get("limit_break", 0)
            rarity_str = f" [★{base_rarity} +{limit_break}]" if limit_break > 0 else f" [★{base_rarity}]"

            elem_str = c.get("element", "なし")
            role_str = c.get("role", "アタッカー")
            gender_str = c.get("gender", "？")

            elem_icon = ELEMENT_ICONS.get(elem_str, "🎨")
            role_icon = ROLE_ICONS.get(role_str, "🛡️")
            char_icon = c.get("icon") if c.get("icon") else elem_icon

            equip_name = c.get("equip") or "なし"
            is_best = c.get("equip") and c.get("equip") == c.get("best_equip")
            equip_bonus_str = " ✨(ATK+20%!)" if is_best else ""

            s_name = c.get("skill_name", "なし")
            s_pow = c.get("skill_pow", 1.0)
            s_type = c.get("skill_type", "physical")

            if s_type == "heal_all":
                skill_info = f"{s_name} (全体回復 / 威力: {s_pow})"
            elif s_type == "heal":
                skill_info = f"{s_name} (単体回復 / 威力: {s_pow})"
            elif s_type == "stun":
                skill_info = f"{s_name} (敵全体麻痺)"
            elif s_type == "magic":
                skill_info = f"{s_name} (魔法攻撃 / 威力: {s_pow})"
            else:
                skill_info = f"{s_name} (物理攻撃 / 威力: {s_pow})"

            status_msg = (
                f"**Lv.{c['level']}** (XP: {c['exp']} /"
                f" {next_exp})\n{elem_icon} **属性**: {elem_str} | {role_icon}"
                f" **ロール**: {role_str} | **性別**: {gender_str}\n🗡️ **装備**:"
                f" {equip_name}{equip_bonus_str}\n❤️ **HP**: {c['hp']} | 🗡️"
                f" **攻撃力**: {c['atk']}\n⚡ **速度**: {c['spd']} | 💖 **回復量**:"
                f" {c['rec']}\n✨ **スキル**: {skill_info}\n\u200b"
            )
            embed.add_field(
                name=f"[{i}] {char_icon} {c['name']}{rarity_str}",
                value=status_msg,
                inline=False,
            )

        return embed

    @discord.ui.button(
        label="◀ 前へ",
        style=discord.ButtonStyle.primary,
        custom_id="prev_page",
    )
    async def prev_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ 他人の操作画面は切り替えられません。", ephemeral=True
            )
            return

        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.create_embed(), view=self
        )

    @discord.ui.button(
        label="次へ ▶",
        style=discord.ButtonStyle.primary,
        custom_id="next_page",
    )
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ 他人の操作画面は切り替えられません。", ephemeral=True
            )
            return

        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.create_embed(), view=self
        )


@bot.tree.command(
    name="status", description="所持キャラクターの一覧とステータスを確認します"
)
async def chars(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    characters = u_data.get("characters", [])

    if not characters:
        await interaction.response.send_message(
            "キャラを所持していません。", ephemeral=True
        )
        return

    view = StatusPaginationView(
        user_id=interaction.user.id,
        user_display_name=interaction.user.display_name,
        characters=characters,
        per_page=4,
    )

    await interaction.response.send_message(
        embed=view.create_embed(), view=view
    )


@bot.tree.command(
    name="party", description="出撃パーティの確認と編成変更を行います"
)
async def party(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)

    embed = discord.Embed(
        title=f"🛡️ {interaction.user.display_name} の出撃パーティ", color=0x1ABC9C
    )

    party_members = [
        u_data["characters"][i]
        for i in u_data["party_indices"]
        if i < len(u_data["characters"])
    ]

    msg = ""
    for idx, c in enumerate(party_members, start=1):
        # /party コマンドの表示名横にもレア度と凸数を表示
        raw_rarity = c.get("rarity", 1)
        if isinstance(raw_rarity, str):
            base_rarity = int(raw_rarity.replace("★", "")) if raw_rarity.replace("★", "").isdigit() else 1
        else:
            base_rarity = int(raw_rarity)
            
        # ⭕️ limit_break をそのまま取得
        limit_break = c.get("limit_break", 0)
        star_str = f"★{base_rarity} +{limit_break}" if limit_break > 0 else f"★{base_rarity}"

        msg += f"**{idx}. {c['name']}** [{star_str}] (Lv.{c['level']} / HP: {c['hp']} / ATK: {c['atk']})\n"

    embed.description = (
        msg
        + "\n👇 下のメニューから出撃させたいメンバーを選択してください（最大3体）。"
    )

    view = PartySelectView(
        interaction.user.id, u_data["characters"], u_data["party_indices"]
    )
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(
    name="gacha", description="虹の欠片やチケットを使って10連ガチャを回します"
)
async def gacha(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    items = u_data.get("items", {})

    rainbow_count = items.get("虹の欠片", 0)
    ticket_count = items.get("ガチャチケ", 0)

    embed = discord.Embed(
        title="🎰 キャラクター召喚（10連ガチャ）",
        description=(
            "10連ガチャを回して新しい仲間を獲得できます！\n\n"
            f"💎 **所持 虹の欠片**: {rainbow_count} 個 (必要: 1000個)\n"
            f"🎫 **所持 ガチャチケ**: {ticket_count} 枚 (必要: 10枚)\n\n"
            "👇 下のボタンを押してガチャを回してください。"
        ),
        color=0x9B59B6,
    )

    view = GachaView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(
    name="shop", description="ゴールドを使ってアイテムやガチャ箱を購入します"
)
async def shop(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)

    embed = discord.Embed(
        title="🏪 アイテムショップ",
        description=(
            f"💰 **所持金**: {u_data['gold']} G\n\n"
            "📦 **ランダムガチャチケ箱**: 1000 G\n"
            "└ 開封すると **1〜10枚** のガチャチケが出現！\n"
            "🎁 **ランダムご飯ボックス**: 800 G\n"
            "└ 開封すると **ランダムなご飯アイテム 計10個**"
            " が入っているよ！\n\n"
            "👇 下のボタンを押して購入・開封してね！"
        ),
        color=0xF1C40F,
    )
    view = ShopView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


# --------------------------------------------------
# 📬 メール受信・受取コマンド（キャラ受取対応版）
# --------------------------------------------------
@bot.tree.command(
    name="mailbox", description="届いているメールや報酬を確認・受け取ります"
)
async def mailbox(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    mails = u_data.get("mails", [])

    unclaimed_mails = [m for m in mails if not m.get("claimed", False)]

    if not unclaimed_mails:
        await interaction.response.send_message(
            "📬 未受け取りのメールはありません。", ephemeral=True
        )
        return

    total_gold = 0
    total_rainbow = 0
    total_ticket = 0
    received_chars = []
    mail_titles = []

    for m in unclaimed_mails:
        total_gold += m.get("gold", 0)
        total_rainbow += m.get("rainbow", 0)
        total_ticket += m.get("ticket", 0)

        # 👤 添付キャラの処理
        char_name = m.get("char_name")
        char_count = m.get("char_count", 1)  # 👈 メールに個数が指定されていれば取得（無ければ1体）
        if char_name:
            template = next(
                (c for c in GACHA_POOL if c["name"] == char_name), None
            )
            if template:
                user_chars = u_data.setdefault("characters", [])
                existing_char = next(
                    (c for c in user_chars if c["name"] == char_name), None
                )

                if existing_char:
                    # すでに所持している場合：純粋に所持数(count)のみを加算
                    # ※ limit_break（限界突破数）は変更せず独立して維持
                    existing_char["count"] = existing_char.get("count", 1) + char_count
                    received_chars.append(f"{char_name} ×{char_count} (所持数: {existing_char['count']})")
                else:
                    # 未所持の場合：新規作成
                    new_char = copy.deepcopy(template)
                    new_char["count"] = char_count
                    new_char["level"] = 1
                    new_char["exp"] = 0
                    new_char["limit_break"] = 0  # 👈 限界突破は0で初期化
                    user_chars.append(new_char)
                    received_chars.append(f"{char_name} ×{char_count} (新規獲得!)")

        m["claimed"] = True
        mail_titles.append(m.get("title", "無題のメール"))

    # 報酬を反映
    u_data["gold"] += total_gold
    u_data["items"]["虹の欠片"] = (
        u_data["items"].get("虹の欠片", 0) + total_rainbow
    )
    u_data["items"]["ガチャチケ"] = (
        u_data["items"].get("ガチャチケ", 0) + total_ticket
    )
    save_data()

    embed = discord.Embed(
        title="🎁 メール報酬を受け取りました！",
        description="\n".join([f"・{t}" for t in mail_titles]),
        color=0x2ECC71,
    )

    reward_msg = (
        f"💰 **ゴールド**: +{total_gold} G\n"
        f"💎 **虹の欠片**: +{total_rainbow} 個\n"
        f"🎫 **ガチャチケ**: +{total_ticket} 枚"
    )
    if received_chars:
        reward_msg += f"\n👤 **獲得キャラ**: " + ", ".join(received_chars)

    embed.add_field(name="獲得アイテム", value=reward_msg, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ エラー: DISCORD_BOT_TOKEN が環境変数に設定されていません。")
