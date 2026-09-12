import random
from collections import Counter
import discord
from discord import app_commands
from discord.ext import commands

# 🔻 database.py など、FOOD_ITEMS が定義されているファイルからインポートしてください
from database import user_data, get_user_profile, save_data, FOOD_ITEMS


class UseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------------------------------------------------
    # 📦 直接使用可能なアイテムの定義リスト
    # --------------------------------------------------
    USABLE_ITEMS = [
        "ランダムご飯ボックス",  # 今後追加したい使用可能アイテムがあればここに追加
        "ご飯ランダムボックス"
    ]

    # オートコンプリート（ユーザーが持っている「使用可能アイテム」のみ補完表示）
    async def item_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        u_data = get_user_profile(interaction.user.id)
        items = u_data.get("items", {})

        choices = []
        for item_name, count in items.items():
            if count > 0 and item_name in self.USABLE_ITEMS and current.lower() in item_name.lower():
                choices.append(app_commands.Choice(name=f"{item_name} (所持: {count})", value=item_name))

        return choices[:25]

    @app_commands.command(name="use", description="所持しているアイテム（ボックスなど）を使用します")
    @app_commands.autocomplete(item_name=item_autocomplete)
    @app_commands.describe(item_name="使用するアイテムを選択してください")
    async def use_item(self, interaction: discord.Interaction, item_name: str):
        u_data = get_user_profile(interaction.user.id)
        user_items = u_data.setdefault("items", {})

        current_count = user_items.get(item_name, 0)
        if current_count <= 0:
            await interaction.response.send_message(
                f"❌ **{item_name}** を持っていません！", ephemeral=True
            )
            return

        # ==================================================
        # 🎁 「ごはんランダムボックス」の開封処理（10連抽選）
        # ==================================================
        if item_name in ("ランダムご飯ボックス", "ご飯ランダムボックス"):
            # 外部参照した FOOD_ITEMS がリスト形式か辞書形式かで判定
            if isinstance(FOOD_ITEMS, list):
                food_list = FOOD_ITEMS
            elif isinstance(FOOD_ITEMS, dict):
                food_list = [{"name": k, **v} for k, v in FOOD_ITEMS.items()]
            else:
                await interaction.response.send_message(
                    "❌ ごはんデータの設定にエラーが発生しました。", ephemeral=True
                )
                return

            if not food_list:
                await interaction.response.send_message(
                    "❌ ボックスからでるアイテムが登録されていません。", ephemeral=True
                )
                return

            # 1. ボックスを1つ消費
            user_items[item_name] -= 1
            if user_items[item_name] <= 0:
                del user_items[item_name]

            # 2. FOOD_ITEMS 内の weight（確率）を参照して 10個 抽選
            weights = [item.get("weight", 1) for item in food_list]
            obtained_items = random.choices(food_list, weights=weights, k=10)

            # 3. 獲得アイテムの集計（例: {"高級なお肉": 2, "普通のおにぎり": 8}）
            obtained_counts = Counter()
            max_exp_in_session = 0

            for obtained_item in obtained_items:
                name = obtained_item.get("name", "謎のごはん")
                exp = obtained_item.get("bond_exp", obtained_item.get("exp", 10))

                obtained_counts[name] += 1
                if exp > max_exp_in_session:
                    max_exp_in_session = exp

                # ユーザーのインベントリに追加
                user_items[name] = user_items.get(name, 0) + 1

            save_data()

            # 表示用の文字列を作成（例: "・**高級なお肉** × 2\n・**普通のおにぎり** × 8"）
            result_text_lines = [f"・**{name}** × {count}" for name, count in obtained_counts.items()]
            result_text = "\n".join(result_text_lines)

            # レア度演出（出た中で一番高価/効果が高い食べ物に応じて色を変更）
            color = 0x3498DB
            if max_exp_in_session >= 100:
                color = 0xE67E22
            elif max_exp_in_session >= 40:
                color = 0x9B59B6

            embed = discord.Embed(
                title="🎁 ボックスを開封しました！（10連）",
                description=f"**{item_name}** から10個のアイテムが出てきました！",
                color=color
            )
            embed.add_field(
                name="🍱 入手した食べ物一覧",
                value=result_text,
                inline=False
            )
            embed.set_footer(text=f"残り {item_name}: {user_items.get(item_name, 0)}個")

            await interaction.response.send_message(embed=embed)

        else:
            await interaction.response.send_message(
                f"❌ **{item_name}** は直接使用できるアイテムではありません。",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(UseCog(bot))
