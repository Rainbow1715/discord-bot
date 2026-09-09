import discord
from discord.ext import commands
from database import user_data, save_data

# --------------------------------------------------
# 🏆 実績の定義リスト
# --------------------------------------------------
ACHIEVEMENTS = {
    "first_win": {
        "title": "🏆 はじめての勝利",
        "desc": "バトルで1回勝利する",
        "reward_gold": 500,
        "reward_rainbow": 0,
    },
    "win_10": {
        "title": "⚔️ 百戦錬磨の兆し",
        "desc": "バトルで10回勝利する",
        "reward_gold": 1000,
        "reward_rainbow": 100,
    },
    "gacha_10": {
        "title": "🎰 ガチャ中毒",
        "desc": "ガチャを累計10回引く",
        "reward_gold": 0,
        "reward_rainbow": 300,
    }
}

# 📢 実績通知を送るチャンネル名
LOG_CHANNEL_NAME = "実績解除ログ"


# --------------------------------------------------
# ⚔️ バトル勝利時の自動実績チェックまとめ
# --------------------------------------------------
async def on_battle_win(interaction: discord.Interaction, u_data: dict):
    """バトル勝利時に呼び出され、カウントアップと実績解除を一括処理する関数"""
    # 勝利数をカウントアップ
    u_data["win_count"] = u_data.get("win_count", 0) + 1

    # 初勝利実績のチェック
    await check_and_unlock_achievement(interaction, "first_win")

    # 10勝実績のチェック
    if u_data["win_count"] >= 10:
        await check_and_unlock_achievement(interaction, "win_10")


# --------------------------------------------------
# 🔓 実績解除・通知共通関数
# --------------------------------------------------
async def check_and_unlock_achievement(interaction: discord.Interaction, achievement_id: str):
    """実績条件を満たした時に呼び出す関数"""
    u_id = interaction.user.id
    u_data = user_data.get(u_id)
    if not u_data:
        return

    # ユーザーデータ内に実績用の領域がなければ作成
    if "unlocked_achievements" not in u_data:
        u_data["unlocked_achievements"] = []

    # すでに解除済みの場合はスルー
    if achievement_id in u_data["unlocked_achievements"]:
        return

    # 実績データ取得
    ach = ACHIEVEMENTS.get(achievement_id)
    if not ach:
        return

    # 1. データ更新（解除フラグ ＆ 報酬付与）
    u_data["unlocked_achievements"].append(achievement_id)
    u_data["gold"] = u_data.get("gold", 0) + ach["reward_gold"]
    
    if "items" not in u_data:
        u_data["items"] = {}
    u_data["items"]["虹の欠片"] = u_data["items"].get("虹の欠片", 0) + ach["reward_rainbow"]
    
    save_data()

    # --------------------------------------------------
    # 🔔 通知①：本人への専用メッセージ（Followup / Ephemeral）
    # --------------------------------------------------
    reward_text = []
    if ach["reward_gold"] > 0:
        reward_text.append(f"💰 {ach['reward_gold']} G")
    if ach["reward_rainbow"] > 0:
        reward_text.append(f"💎 虹の欠片 {ach['reward_rainbow']}個")
    
    reward_str = " / ".join(reward_text) if reward_text else "なし"

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
    # 📢 通知②：実績専用チャンネルへの自動投稿
    # --------------------------------------------------
    try:
        # サーバー内の全テキストチャンネルから名前で検索
        target_channel = discord.utils.get(interaction.guild.text_channels, name=LOG_CHANNEL_NAME)
        
        if target_channel:
            embed_log = discord.Embed(
                title="📢 実績解除ニュース！",
                description=f"**{interaction.user.display_name}** さんが実績【**{ach['title']}**】を解除しました！👏",
                color=0x3498DB
            )
            await target_channel.send(embed=embed_log)
            print(f"✅ 実績通知を送信しました: #{LOG_CHANNEL_NAME}")
        else:
            # チャンネルが見つからない場合ログを出す
            print(f"⚠️ チャンネル '#{LOG_CHANNEL_NAME}' が見つかりませんでした。Botの権限かチャンネル名を確認してください。")
            
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
            embed.add_field(
                name=f"{ach['title']} ({status})",
                value=f"{ach['desc']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
