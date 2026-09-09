import discord
from discord import app_commands
from discord.ext import commands
from database import user_data, get_user_profile, save_data

# --------------------------------------------------
# 🌟 レアリティ(★)ごとの必要条件・コスト定義
# --------------------------------------------------
# キー: 現在のレアリティ文字列
RANKUP_REQUIREMENTS = {
    "★1": 15,  # 必要同キャラ数
    "★2": 20,
    "★3": 25,
    "★4": 50,
}

RANKUP_GOLD = {
    "★1": 5000,    # 必要ゴールド
    "★2": 15000,
    "★3": 30000,
    "★4": 100000,
}

# レアリティの進化順
NEXT_RARITY = {
    "★1": "★2",
    "★2": "★3",
    "★3": "★4",
    "★4": "★5",
}


# --------------------------------------------------
# 🎛️ ★上げ選択用 UI View
# --------------------------------------------------
class RankUpSelectView(discord.ui.View):
    def __init__(self, user_id: int, characters: list, user_gold: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.characters = characters
        self.user_gold = user_gold

        options = []
        for idx, c in enumerate(characters[:25]):  # メニュー制限上限25件
            rarity = c.get("rarity", "★3")
            count = c.get("count", 1)
            req_count = RANKUP_REQUIREMENTS.get(rarity)
            req_gold = RANKUP_GOLD.get(rarity, 0)
            
            if req_count:
                req_str = f"{req_count}体/{req_gold:,}G"
                can_up = (count >= req_count and user_gold >= req_gold)
            else:
                req_str = "MAX"
                can_up = False

            options.append(
                discord.SelectOption(
                    label=f"[{rarity}] {c['name']} (所持: {count}体)",
                    value=str(idx),
                    description=f"次ランク条件: {req_str}",
                    emoji="🌟" if can_up else "👤"
                )
            )

        select = discord.ui.Select(
            placeholder="★を上げたいキャラクターを選んでください",
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

        c_idx = int(self.children[0].values[0])
        u_data = get_user_profile(self.user_id)
        char = u_data["characters"][c_idx]

        curr_rarity = char.get("rarity", "★3")
        count = char.get("count", 1)
        curr_gold = u_data.get("gold", 0)

        # ★5（カンスト）のチェック
        if curr_rarity not in RANKUP_REQUIREMENTS:
            await interaction.response.send_message(
                f"❌ **{char['name']}** は既に最高レアリティ ({curr_rarity}) です！",
                ephemeral=True
            )
            return

        req_count = RANKUP_REQUIREMENTS[curr_rarity]
        req_gold = RANKUP_GOLD[curr_rarity]

        # 1. 必要キャラ数チェック
        if count < req_count:
            await interaction.response.send_message(
                f"❌ 素材（キャラ数）が不足しています！\n"
                f"・**{char['name']}** の現在の所持数: **{count}** 体\n"
                f"・{curr_rarity} ➔ {NEXT_RARITY[curr_rarity]} に必要な数: **{req_count}** 体（あと {req_count - count} 体必要）",
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
        # ✨ ★上げ実行処理
        # --------------------------------------------------
        # 💰 1. コストの消費
        u_data["gold"] -= req_gold  # ゴールド消費
        consume_count = req_count - 1
        char["count"] -= consume_count  # 同キャラ消費（1体残す）

        # 🌟 2. ★の引き上げ
        next_r = NEXT_RARITY[curr_rarity]
        char["rarity"] = next_r

        # 📈 3. ステータス＆スキル倍率の強化
        # ステータスアップ (+20%)
        hp_up = int(char["hp"] * 0.20)
        atk_up = int(char["atk"] * 0.20)
        char["hp"] += hp_up
        char["atk"] += atk_up

        # スキル威力の強化 (倍率 +0.3 増加)
        old_pow = char.get("skill_pow", 1.0)
        new_pow = round(old_pow + 0.3, 2)
        char["skill_pow"] = new_pow

        save_data()

        embed = discord.Embed(
            title="🌟 レアリティアップ完了！",
            description=f"**{char['name']}** が **{curr_rarity} ➔ {next_r}** に強化されました！",
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

    @app_commands.command(name="rankup", description="重複した同キャラとゴールドを消費してキャラクターの★を上げます")
    async def rankup(self, interaction: discord.Interaction):
        u_data = get_user_profile(interaction.user.id)
        characters = u_data.get("characters", [])
        user_gold = u_data.get("gold", 0)

        if not characters:
            await interaction.response.send_message("❌ 所持しているキャラクターがいません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="🌟 キャラクターの★上げ（限界突破）",
            description=(
                "同キャラとゴールドを消費して★を上昇させることができます。\n"
                "★が上がると**ステータスUP**や**スキル威力UP**が得られます！\n\n"
                "📜 **必要コスト一覧:**\n"
                "・★1 ➔ ★2: 15体 / 5,000 G\n"
                "・★2 ➔ ★3: 20体 / 15,000 G\n"
                "・★3 ➔ ★4: 25体 / 30,000 G\n"
                "・★4 ➔ ★5: 50体 / 100,000 G"
            ),
            color=0xF1C40F
        )

        view = RankUpSelectView(interaction.user.id, characters, user_gold)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(RankUpCog(bot))
