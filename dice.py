import random
import discord
from discord import app_commands

# --------------------------------------------------
# 1. グループごとの絵文字リストを定義
# "<:custom_emoji_name:123456789012345678>",
# --------------------------------------------------
EMOJI_GROUPS = {
    "A": [
        "🔥", "⚔️", "🛡️", "⚡"  # Aグループの絵文字（カスタム絵文字も可）
    ],
    "B": [
        "🌸", "🍀", "🌙", "💎"  # Bグループの絵文字
    ]
}

# --------------------------------------------------
# 2. スラッシュコマンド（/dice）の定義
# --------------------------------------------------
@tree.command(name="dice", description="指定したグループの中からランダムで絵文字を選びます")
@app_commands.choices(
    group=[
        app_commands.Choice(name="Aグループ", value="A"),
        app_commands.Choice(name="Bグループ", value="B"),
        app_commands.Choice(name="AとBの両方", value="AB"),
    ]
)
async def dice(interaction: discord.Interaction, group: app_commands.Choice[str]):
    selected_val = group.value
    target_emojis = []

    # 選択されたグループに応じて対象の絵文字リストを準備
    if selected_val == "A":
        target_emojis = EMOJI_GROUPS["A"]
    elif selected_val == "B":
        target_emojis = EMOJI_GROUPS["B"]
    elif selected_val == "AB":
        # AとBのリストを合体させる
        target_emojis = EMOJI_GROUPS["A"] + EMOJI_GROUPS["B"]

    # リストが空でなければランダムで1つ選ぶ
    if target_emojis:
        chosen_emoji = random.choice(target_emojis)
        await interaction.response.send_message(
            f"🎲 **{interaction.user.display_name}** さんのダイス結果（{group.name}）： {chosen_emoji}"
        )
    else:
        await interaction.response.send_message(
            "絵文字リストが空です。", ephemeral=True
        )
