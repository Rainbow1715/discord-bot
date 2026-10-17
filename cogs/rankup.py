import discord
from discord import app_commands
from discord.ext import commands
from database import user_data, get_user_profile, save_data, GACHA_POOL

# --------------------------------------------------
# 🌟 凸段階ごとの必要条件・コスト定義
# --------------------------------------------------
RANKUP_REQUIREMENTS = {
    "+1": 15,
    "+2": 20,
    "+3": 25,
    "+4": 50,
    "+5": 50,
}

RANKUP_GOLD = {
    "+1": 5000,
    "+2": 15000,
    "+3": 30000,
    "+4": 100000,
    "+5": 500000,
}

# 次の凸段階へのマッピング
NEXT_LB = {
    "+0": "+1",
    "+1": "+2",
    "+2": "+3",
    "+3": "+4",
    "+4": "+5",
}


# --------------------------------------------------
# 🎛️ ★上げ・凸上げ選択用 UI View
# --------------------------------------------------
class RankUpSelectView(discord.ui.View):
    def __init__(self, user_id: int, characters: list, user_gold: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.characters = characters
        self.user_gold = user_gold

        options = []
        for idx, c in enumerate(characters[:25]):
            rarity = c.get("rarity", "★3")
            # 凸数（数値または文字列）を "+0" 〜 "+5" の形式に正規化
            lb_val = c.get("limit_break", 0)
            if isinstance(lb_val, int):
                lb_key = f"+{lb_val}"
            else:
                lb_key = lb_val if lb_val.startswith("+") else f"+{lb_val}"

            # 次の凸段階のキーを取得
            next_key = NEXT_LB.get(lb_key)

            if next_key and next_key in RANKUP_REQUIREMENTS:
                req_count = RANKUP_REQUIREMENTS[next_key]
                req_gold = RANKUP_GOLD[next_key]
                req_str = f"{req_count}体/{req_gold:,}G"
                count = c.get("count", 1)
                can_up = (count >= req_count and user_gold >= req_gold)
            else:
                req_str = "MAX (5凸完凸)"
                can_up = False

            # 表示ラベル（例: [★3 +1] キャラ名）
            display_lb = lb_key if lb_key != "+0" else ""
            options.append(
                discord.SelectOption(
                    label=f"[{rarity}{display_lb}] {c['name']} (所持: {c.get('count', 1)}体)",
                    value=c["name"],
                    description=f"次凸条件 ({next_key if next_key else 'MAX'}): {req_str}",
                    emoji="🌟" if can_up else "👤"
                )
            )

        select = discord.ui.Select(
            placeholder="限界突破（凸）させたいキャラクターを選んでください",
            min_values=1,
            max_values=1,
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 他人の画面は操作できません。", ephemeral=True)
            return

        selected_name = self.children[0].values[0]
        u_data = get_user_profile(self.user_id)
        
        char = next((c for c in u_data.get("characters", []) if c["name"] == selected_name), None)

        if not char:
            await interaction.response.send_message("❌ 対象のキャラクターが見つかりませんでした。", ephemeral=True)
            return

        rarity = char.get("rarity", "★3")
        lb_val = char.get("limit_break", 0)
        if isinstance(lb_val, int):
            lb_key = f"+{lb_val}"
        else:
            lb_key = lb_val if lb_val.startswith("+") else f"+{lb_val}"

        next_key = NEXT_LB.get(lb_key)
        count = char.get("count", 1)
        curr_gold = u_data.get("gold", 0)

        # 5凸（カンスト）のチェック
        if not next_key or next_key not in RANKUP_REQUIREMENTS:
            await interaction.response.send_message(
                f"❌ **{char['name']}** は既に最大限界突破 (5凸) に達しています！",
                ephemeral=True
            )
            return

        req_count = RANKUP_REQUIREMENTS[next_key]
        req_gold = RANKUP_GOLD[next_key]

        # 1. 必要キャラ数チェック
        if count < req_count:
            await interaction.response.send_message(
                f"❌ 素材（キャラ数）が不足しています！\n"
                f"・**{char['name']}** の現在の所持数: **{count}** 体\n"
                f"・{lb_key} ➔ {next_key} に必要な数: **{req_count}** 体（あと {req_count - count} 体必要）",
                ephemeral=True
            )
            return

        # 2. 所持ゴールドチェック
        if curr_gold < req_gold:
            await interaction.response.send_message(
                f"❌ ゴールドが不足しています！\n"
                f"・現在の所持金: **{curr_gold:,}** G\n"
                f"・必要ゴールド: **{req_gold:,}** G（あと {req_gold - curr_gold:,} G 必要）",
                ephemeral=True
            )
            return

        # --------------------------------------------------
        # ✨ 限界突破実行処理
        # --------------------------------------------------
        u_data["gold"] -= req_gold  # ゴールド消費
        consume_count = req_count - 1
        char["count"] -= consume_count  # 同キャラ消費（1体残す）

        # 凸数の更新（数値として保存：例 +1 なら 1）
        new_int_lb = int(next_key.replace("+", ""))
        char["limit_break"] = new_int_lb

        # 📈 ステータス＆スキル倍率の強化
        template = next((c for c in GACHA_POOL if c["name"] == char["name"]), None)

        if template:
            base_hp = template.get("hp", 100)
            base_atk = template.get("atk", 10)
            hp_up = max(1, int(base_hp * 0.10))
            atk_up = max(1, int(base_atk * 0.20))
        else:
            hp_up = 10
            atk_up = 2

        char["hp"] += hp_up
        if "max_hp" in char:
            char["max_hp"] += hp_up
            
        char["atk"] += atk_up

        # スキル威力の強化 (倍率 +0.3 増加)
        old_pow = char.get("skill_pow", 1.0)
        new_pow = round(old_pow + 0.3, 2)
        char["skill_pow"] = new_pow

        save_data()

        embed = discord.Embed(
            title="🌟 限界突破完了！",
            description=f"**{char['name']}** が **{lb_key} ➔ {next_key}** に限界突破しました！",
            color=0xF1C40F
        )
        embed.add_field(
            name="💸 消費されたコスト",
            value=f"・同個体: **{consume_count}** 体 (残り: {char['count']}体)\n"
                  f"・ゴールド: **{req_gold:,}** G (残金: {u_data['gold']:,} G)",
            inline=False
        )
        embed.add_field(name="❤️ HP", value=f"+{hp_up} ➔ **{char['hp']}**", inline=True)
        embed.add_field(name="🗡️ 攻撃力", value=f"+{atk_up} ➔ **{char['atk']}**", inline=True)
        embed.add_field(name="✨ スキル威力", value=f"{old_pow}x ➔ **{new_pow}x**", inline=False)

        await interaction.response.edit_message(embed=embed, view=None)


# --------------------------------------------------
# 💬 RankUpCog (スラッシュコマンド)
# --------------------------------------------------
class RankUpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rankup", description="重複した同キャラとゴールドを消費してキャラクターの限界突破（最大5凸）を行います")
    async def rankup(self, interaction: discord.Interaction):
        u_data = get_user_profile(interaction.user.id)
        characters = u_data.get("characters", [])
        user_gold = u_data.get("gold", 0)

        if not characters:
            await interaction.response.send_message("❌ 所持しているキャラクターがいません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="🌟 キャラクターの限界突破（凸上げ）",
            description=(
                "同キャラとゴールドを消費して最大5回まで限界突破できます。\n"
                "突破すると**ステータスUP**や**スキル威力UP**が得られます！\n\n"
                "📜 **必要コスト一覧:**\n"
                "・+0 ➔ +1: 15体 / 5,000 G\n"
                "・+1 ➔ +2: 20体 / 15,000 G\n"
                "・+2 ➔ +3: 25体 / 30,000 G\n"
                "・+3 ➔ +4: 50体 / 100,000 G\n"
                "・+4 ➔ +5: 50体 / 500,000 G"
            ),
            color=0xF1C40F
        )

        view = RankUpSelectView(interaction.user.id, characters, user_gold)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(RankUpCog(bot))
