import discord
from discord.ext import commands
from database import user_data, save_data

# --------------------------------------------------
# 🏆 実績の定義リスト
# --------------------------------------------------
ACHIEVEMENTS = {
    "first_win": {
        "title": "🔰 はじめての勝利",
        "desc": "バトルで1回勝利する",
        "reward_rainbow": 500,
    },
    "win_10": {
        "title": "⚔️ 百戦錬磨の兆し",
        "desc": "バトルで10回勝利する",
        "reward_rainbow": 1000,
    },
    "win_50": {
        "title": "⚔️ あと半分",
        "desc": "バトルで50回勝利する",
        "reward_rainbow": 5000,
    },
    "gacha_1": {
        "title": "🔰 初めてのガチャ",
        "desc": "ガチャを累計1回引く",
        "reward_rainbow": 300,
    },
    "gacha_10": {
        "title": "🎰 ガチャ中毒",
        "desc": "ガチャを累計10回引く",
        "reward_rainbow": 800,
    },
    "gacha_50": {
        "title": "🎰 もうちょいで100",
        "desc": "ガチャを累計50回引く",
        "reward_rainbow": 1000,
    },
    # 🆕 特定キャラ編成で勝利の実績
    "win_siera_retya": {
        "title": "😰 ど、同一人物……",
        "desc": "竹村しえら と れーちゃん を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
}

# 📢 実績通知を送るチャンネルID
LOG_CHANNEL_ID = 1547122457062940712


# --------------------------------------------------
# ⚔️ バトル勝利時の自動実績チェック
# --------------------------------------------------
async def on_battle_win(interaction: discord.Interaction, u_data: dict):
    """バトル勝利時に呼び出され、カウントアップと実績解除を一括処理する関数"""
    u_data["win_count"] = u_data.get("win_count", 0) + 1

    await check_and_unlock_achievement(interaction, "first_win")

    if u_data["win_count"] >= 10:
        await check_and_unlock_achievement(interaction, "win_10")
    if u_data["win_count"] >= 50:
        await check_and_unlock_achievement(interaction, "win_50")

    # --------------------------------------------------
    # 👭 複数キャラ（コンビ・グループ）編成チェック
    # --------------------------------------------------
    # party_indices と characters から現在編成中のキャラ名を取得
    party_indices = u_data.get("party_indices", [])
    characters = u_data.get("characters", [])

    party_char_names = set()
    for idx in party_indices:
        if isinstance(idx, int) and idx < len(characters):
            char_data = characters[idx]
            if isinstance(char_data, dict):
                party_char_names.add(char_data.get("name"))

    # 竹村しえら ＆ れーちゃん が両方パーティにいるか？
    target_pair = {"竹村しえら", "れーちゃん"}
    if target_pair.issubset(party_char_names):
        await check_and_unlock_achievement(interaction, "win_siera_retya")
    else:
        print(f"DEBUG: 条件未達成。不足しているキャラ -> {target_pair - party_char_names}")


# --------------------------------------------------
# 🎰 ガチャ実行時の自動実績チェック
# --------------------------------------------------
async def on_gacha_draw(interaction: discord.Interaction, u_data: dict):
    """ガチャを引いた時に呼び出し、実績判定を行う関数"""
    count = u_data.get("gacha_count", 0)

    if count >= 1:
        await check_and_unlock_achievement(interaction, "gacha_1")
    if count >= 10:
        await check_and_unlock_achievement(interaction, "gacha_10")
    if count >= 50:
        await check_and_unlock_achievement(interaction, "gacha_50")


# --------------------------------------------------
# 🔓 実績解除・通知共通関数
# --------------------------------------------------
async def check_and_unlock_achievement(interaction: discord.Interaction, achievement_id: str):
    """実績条件を満たした時に呼び出す関数"""
    u_id = interaction.user.id
    u_data = user_data.get(u_id)
    if not u_data:
        return

    if "unlocked_achievements" not in u_data:
        u_data["unlocked_achievements"] = []

    # 既に解除済みの場合は処理しない
    if achievement_id in u_data["unlocked_achievements"]:
        return

    ach = ACHIEVEMENTS.get(achievement_id)
    if not ach:
        return

    # データ更新（解除フラグ ＆ 虹の欠片付与）
    u_data["unlocked_achievements"].append(achievement_id)
    
    reward_rainbow = ach.get("reward_rainbow", 0)
    
    if "items" not in u_data:
        u_data["items"] = {}
    u_data["items"]["虹の欠片"] = u_data["items"].get("虹の欠片", 0) + reward_rainbow
    
    save_data()

    # --------------------------------------------------
    # 🔔 通知①：本人への専用メッセージ（Ephemeral）
    # --------------------------------------------------
    reward_str = f"💎 虹の欠片 {reward_rainbow}個" if reward_rainbow > 0 else "なし"

    embed_user = discord.Embed(
        title="🎉 実績を解除しました！",
        description=f"**{ach['title']}**\n└ {ach['desc']}\n\n🎁 **獲得報酬**: {reward_str}",
        color=0xF1C40F
    )
    
    try:
        await interaction.followup.send(embed=embed_user, ephemeral=True)
    except Exception as e:
        print(f"本人への実績通知エラー: {e}")

    # --------------------------------------------------
    # 📢 通知②：チャンネルIDへ直接テキストで投稿
    # --------------------------------------------------
    try:
        target_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        
        if target_channel:
            await target_channel.send(f"{interaction.user.mention} が 実績【{ach['title']}】を解除しました！")
            print(f"✅ 実績ログを送信しました (ID: {LOG_CHANNEL_ID})")
        else:
            print(f"⚠️ 指定されたチャンネルID ({LOG_CHANNEL_ID}) が見つかりませんでした。")

    except Exception as e:
        print(f"ログチャンネルへの実績通知エラー: {e}")


# --------------------------------------------------
# 🤖 実績確認コマンド (/achievements)
# --------------------------------------------------
class AchievementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="achievements", description="実績の獲得状況を確認します")
    async def achievements(self, interaction: discord.Interaction):
        u_data = user_data.get(interaction.user.id, {})
        unlocked = u_data.get("unlocked_achievements", [])

        embed = discord.Embed(
            title=f"🏆 {interaction.user.display_name} の実績一覧",
            color=0xF1C40F
        )

        for ach_id, ach in ACHIEVEMENTS.items():
            status = "✅ 達成済み" if ach_id in unlocked else "🔒 未達成"
            reward_val = ach.get("reward_rainbow", 0)
            reward_info = f" (🎁 虹の欠片 {reward_val}個)" if reward_val > 0 else ""
            
            embed.add_field(
                name=f"{ach['title']} ({status})",
                value=f"{ach['desc']}{reward_info}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
