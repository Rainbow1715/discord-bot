import discord
from database import user_data, save_data
from discord.ext import commands

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
    "win_100": {
        "title": "⚔️ やるやん",
        "desc": "バトルで100回勝利する",
        "reward_rainbow": 10000,
    },
    "win_200": {
        "title": "⚔️ （ドン引き）",
        "desc": "バトルで200回勝利する",
        "reward_rainbow": 10000,
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
    "gacha_100": {
        "title": "🎰 真のガチャ中毒",
        "desc": "ガチャを累計100回引く",
        "reward_rainbow": 3000,
    },
    # 🆕 特定キャラ編成で勝利の実績
    "win_siera_retya": {
        "title": "😰 ど、同一人物……",
        "desc": "竹村しえら と れーちゃん を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_siera_x3": {
        "title": "😰 ど、同一人物……②",
        "desc": "いずれかの 竹村しえら を3人編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_reo": {
        "title": "🤨 誰だお前？",
        "desc": "レオ と レオ(仮面ライダーパロ) を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_marin_orihara": {
        "title": "😰 なんでそんなことしたの？",
        "desc": "茉鈴 と 折原和也 を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_reo_roi": {
        "title": "🧐 なんでこんなことしたの？",
        "desc": "レオ と ロイ を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_roi_orihara_tatuya": {
        "title": "😟 カス三人衆を連れてきたよ①",
        "desc": "ロイ 折原和也 神明龍矢 を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_roi_sara_tatuya": {
        "title": "😟 カス三人衆を連れてきたよ②",
        "desc": "ロイ サラ 神明龍矢 を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_reo_sara": {
        "title": "🤩 弱虫毛虫、意気地なし！",
        "desc": "レオ サラ を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    # 👤 特定キャラ入手実績
    "get_kami": {
        "title": "❔ なんで？",
        "desc": "白黒レイ を獲得する",
        "reward_rainbow": 17000,
    },
    "get_rider_siera": {
        "title": "🚀 宇宙、キター！ ……はっず",
        "desc": "しえら(仮面ライダーパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_rider_reo": {
        "title": "🐉 今の俺は、負ける気がしねぇ！",
        "desc": "レオ(仮面ライダーパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_trickal_rucia": {
        "title": "🪅 一緒に遊ばない？",
        "desc": "ルシア(トリッカルパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_trickal_mukuro": {
        "title": "🙌 ぼくが遊びにきたのだよ。",
        "desc": "ムクロ(トリッカルパロ) を獲得する",
        "reward_rainbow": 200,
    },
    # 💔 敗北系実績
    "first_lose": {
        "title": "🔰 最初の挫折",
        "desc": "初めてバトルで敗北する",
        "reward_rainbow": 200,
    },
    "lose_10": {
        "title": "🩹 七転び八起き",
        "desc": "累計10回バトルで敗北する",
        "reward_rainbow": 350,
    },
    # 👹 イベントボス撃破実績
    "kill_roi": {
        "title": "⚔️ カス討伐：ロイ",
        "desc": "イベント戦で ロイ を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_orihara": {
        "title": "⚔️ カス討伐：折原和也",
        "desc": "イベント戦で 折原和也 を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_tatsuya": {
        "title": "⚔️ カス討伐：神明龍矢",
        "desc": "イベント戦で 神明龍矢 を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_sara": {
        "title": "⚔️ カス討伐：サラ",
        "desc": "イベント戦で サラ を撃破する",
        "reward_rainbow": 1000,
    },  # 修正: カンマと閉じカッコを追加
    # 🍽️ 飯実績
    "eat_siera": {
        "title": "🍽️ しえらの嫌いなもの",
        "desc": "竹村しえら に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_retyan": {
        "title": "🍽️ れーちゃんの嫌いなもの",
        "desc": "れーちゃん に嫌いなものを食べさせた",
        "reward_rainbow": 150,
    },
    "eat_reo": {
        "title": "🍽️ レオの嫌いなもの",
        "desc": "レオ に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_touwata": {
        "title": "🍽️ 唐綿さんの嫌いなもの",
        "desc": "Gerânio に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_skrei": {
        "title": "🍽️ xX神Xxの嫌いなもの",
        "desc": "白黒レイ に嫌いなものを食べさせた",
        "reward_rainbow": 500,
    },
    "eat_marin": {
        "title": "🍽️ 茉鈴の嫌いなもの",
        "desc": "茉鈴 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_syuuto": {
        "title": "🍽️ 柊人の嫌いなもの",
        "desc": "橘柊人 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_mikan": {
        "title": "🍽️ 河野蜜柑の嫌いなもの",
        "desc": "河野蜜柑 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_roi": {
        "title": "🍽️ ロイの嫌いなもの",
        "desc": "ロイ に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_orihara": {
        "title": "🍽️ 折原さんの嫌いなもの",
        "desc": "折原和也 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_tatuya": {
        "title": "🍽️ 神明龍矢の嫌いなもの",
        "desc": "神明龍矢 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eat_sara": {
        "title": "🍽️ サラの嫌いなもの",
        "desc": "サラ に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
}

LOG_CHANNEL_ID = 1547122457062940712


# --------------------------------------------------
# ⚔️ バトル勝利時の自動実績チェック
# --------------------------------------------------
async def on_battle_win(interaction: discord.Interaction, u_data: dict):
    u_data["win_count"] = u_data.get("win_count", 0) + 1
    win_count = u_data["win_count"]

    await check_and_unlock_achievement(interaction, "first_win")
    if win_count >= 10:
        await check_and_unlock_achievement(interaction, "win_10")
    if win_count >= 50:
        await check_and_unlock_achievement(interaction, "win_50")
    if win_count >= 100:
        await check_and_unlock_achievement(interaction, "win_100")
    if win_count >= 200:  # 追加: win_200 のチェック抜けを補填
        await check_and_unlock_achievement(interaction, "win_200")

    party_indices = u_data.get("party_indices", [])
    characters = u_data.get("characters", [])

    party_names = []
    for idx in party_indices:
        if isinstance(idx, int) and idx < len(characters):
            char_data = characters[idx]
            if isinstance(char_data, dict) and "name" in char_data:
                party_names.append(char_data["name"])

    party_names_set = set(party_names)

    if {"竹村しえら", "れーちゃん"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_siera_retya")

    siera_count = sum(1 for name in party_names if "しえら" in name)
    if siera_count >= 3:
        await check_and_unlock_achievement(interaction, "win_siera_x3")

    if {"レオ", "レオ(仮面ライダーパロ)"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_reo")

    if {"茉鈴", "折原和也"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_marin_orihara")

    if {"レオ", "ロイ"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_reo_roi")

    if {"ロイ", "折原和也", "神明龍矢"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_roi_orihara_tatuya")

    if {"ロイ", "サラ", "神明龍矢"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_roi_sara_tatuya")

    if {"レオ", "サラ"}.issubset(party_names_set):  # 追加: win_reo_sara
        await check_and_unlock_achievement(interaction, "win_reo_sara")


# --------------------------------------------------
# 💔 バトル敗北時の自動実績チェック
# --------------------------------------------------
async def on_battle_lose(interaction: discord.Interaction, u_data: dict):
    u_data["lose_count"] = u_data.get("lose_count", 0) + 1
    lose_count = u_data["lose_count"]

    await check_and_unlock_achievement(interaction, "first_lose")
    if lose_count >= 10:
        await check_and_unlock_achievement(interaction, "lose_10")


# --------------------------------------------------
# 👹 イベントボス撃破時の自動実績チェック
# --------------------------------------------------
async def check_boss_kill_achievements(
    interaction: discord.Interaction, defeated_enemy_names: list
):
    boss_mapping = {
        "ロイ": "kill_roi",
        "折原和也": "kill_orihara",
        "神明龍矢": "kill_tatsuya",
        "サラ": "kill_sara",  # 追加: サラの撃破判定を追加
    }

    for boss_name, ach_id in boss_mapping.items():
        if any(boss_name in enemy_name for enemy_name in defeated_enemy_names):
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# 🎰 ガチャ実行時の自動実績チェック
# --------------------------------------------------
async def on_gacha_draw(interaction: discord.Interaction, u_data: dict):
    count = u_data.get("gacha_count", 0)

    if count >= 1:
        await check_and_unlock_achievement(interaction, "gacha_1")
    if count >= 10:
        await check_and_unlock_achievement(interaction, "gacha_10")
    if count >= 50:
        await check_and_unlock_achievement(interaction, "gacha_50")
    if count >= 100:
        await check_and_unlock_achievement(interaction, "gacha_100")


# --------------------------------------------------
# 🎴 特定キャラ獲得時の自動実績チェック
# --------------------------------------------------
async def check_character_achievements(
    interaction: discord.Interaction,
    u_data: dict,
    obtained_character_names: list,
):
    mapping = {
        "白黒レイ": "get_kami",
        "しえら(仮面ライダーパロ)": "get_rider_siera",
        "レオ(仮面ライダーパロ)": "get_rider_reo",
        "ルシア(トリッカルパロ)": "get_trickal_rucia",
        "ムクロ(トリッカルパロ)": "get_trickal_mukuro",
    }

    for name, ach_id in mapping.items():
        if name in obtained_character_names:
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# 🔓 実績解除・通知共通関数
# --------------------------------------------------
async def check_and_unlock_achievement(
    interaction: discord.Interaction, achievement_id: str
):
    u_id = interaction.user.id
    u_data = user_data.get(u_id)
    if not u_data:
        return

    if "unlocked_achievements" not in u_data:
        u_data["unlocked_achievements"] = []

    if achievement_id in u_data["unlocked_achievements"]:
        return

    ach = ACHIEVEMENTS.get(achievement_id)
    if not ach:
        return

    u_data["unlocked_achievements"].append(achievement_id)
    reward_rainbow = ach.get("reward_rainbow", 0)

    if "items" not in u_data:
        u_data["items"] = {}
    u_data["items"]["虹の欠片"] = (
        u_data["items"].get("虹の欠片", 0) + reward_rainbow
    )

    save_data()

    # 🔔 通知①：本人へのメッセージ（レスポンス状況に応じた安全な送信）
    reward_str = (
        f"💎 虹の欠片 {reward_rainbow}個" if reward_rainbow > 0 else "なし"
    )
    embed_user = discord.Embed(
        title="🎉 実績を解除しました！",
        description=f"**{ach['title']}**\n└ {ach['desc']}\n\n🎁 **獲得報酬**: {reward_str}",
        color=0xF1C40F,
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed_user, ephemeral=True)
        else:
            await interaction.response.send_message(
                embed=embed_user, ephemeral=True
            )
    except Exception as e:
        print(f"本人への実績通知エラー: {e}")

    # 📢 通知②：ログチャンネルへの投稿
    try:
        target_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if target_channel:
            await target_channel.send(
                f"{interaction.user.mention} が 実績【{ach['title']}】を解除しました！"
            )
        else:
            print(
                f"⚠️ 指定されたチャンネルID ({LOG_CHANNEL_ID}) が見つかりませんでした。"
            )
    except Exception as e:
        print(f"ログチャンネルへの実績通知エラー: {e}")


# --------------------------------------------------
# 🤖 実績確認コマンド (/achievements)
# --------------------------------------------------
class AchievementCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="achievements", description="実績の獲得状況を確認します"
    )
    async def achievements(self, interaction: discord.Interaction):
        u_data = user_data.get(interaction.user.id, {})
        unlocked = u_data.get("unlocked_achievements", [])

        embeds = []
        current_embed = discord.Embed(
            title=f"🏆 {interaction.user.display_name} の実績一覧", color=0xF1C40F
        )
        field_count = 0

        # Discordの25フィールド制限対策：20個ごとにEmbedを分割
        for ach_id, ach in ACHIEVEMENTS.items():
            if field_count >= 20:
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title=f"🏆 {interaction.user.display_name} の実績一覧 (続き)",
                    color=0xF1C40F,
                )
                field_count = 0

            status = "✅ 達成済み" if ach_id in unlocked else "🔒 未達成"
            reward_val = ach.get("reward_rainbow", 0)
            reward_info = (
                f" (🎁 虹の欠片 {reward_val}個)" if reward_val > 0 else ""
            )

            current_embed.add_field(
                name=f"{ach['title']} ({status})",
                value=f"{ach['desc']}{reward_info}",
                inline=False,
            )
            field_count += 1

        embeds.append(current_embed)

        # 最初のEmbedを返信し、残りはfollowupで送信
        await interaction.response.send_message(
            embed=embeds[0], ephemeral=True
        )
        for extra_embed in embeds[1:]:
            await interaction.followup.send(embed=extra_embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
