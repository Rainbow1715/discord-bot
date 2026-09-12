import random
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
        "ご飯ランダムボックス",  # 今後追加したい使用可能アイテムがあればここに追加
    ]

    # オートコンプリート（ユーザーが持っている「使用可能アイテム」のみ補完表示）
    async def item_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        u_data = get_user_profile(interaction.user.id)
        items = u_data.get("items", {})

        choices = []
        for item_name, count in items.items():
            # 💡 条件に「使用可能なアイテムリストに含まれているか」を追加
            if count > 0 and item_name in USABLE_ITEMS and current.lower() in item_name.lower():
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
        # 🎁 「ごはんランダムボックス」の開封処理
        # ==================================================
        if item_name == "ごはんランダムボックス":
            # 外部参照した FOOD_ITEMS がリスト形式か辞書形式かで判定
            if isinstance(FOOD_ITEMS, list):
                food_list = FOOD_ITEMS
            elif isinstance(FOOD_ITEMS, dict):
                # 辞書型（{"高級なお肉": {"bond_exp": 50, "weight": 10}, ...} のような構造）の場合
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

            # 2. FOOD_ITEMS 内の weight（重み/確率）を参照して抽選
            # ※ weight 設定がない場合は一律 1（均等確率）として扱います
            weights = [item.get("weight", 1) for item in food_list]
            obtained_item = random.choices(food_list, weights=weights, k=1)[0]

            obtained_name = obtained_item.get("name", "謎のごはん")
            # 「bond_exp」「exp」「value」など、定義されているキーに合わせて参照
            obtained_exp = obtained_item.get("bond_exp", obtained_item.get("exp", 10))

            # 3. インベントリに獲得アイテムを追加
            user_items[obtained_name] = user_items.get(obtained_name, 0) + 1
            save_data()

            # レア度演出（上昇値に応じて色を変更）
            color = 0x3498DB
            if obtained_exp >= 100:
                color = 0xE67E22
            elif obtained_exp >= 40:
                color = 0x9B59B6

            embed = discord.Embed(
                title="🎁 ボックスを開封しました！",
                description=f"**{item_name}** から以下のアイテムが出てきました！",
                color=color
            )
            embed.add_field(
                name="🍱 入手アイテム",
                value=f"**{obtained_name}** × 1\n（なつき度上昇値: +{obtained_exp}）",
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
