import re
import time
import discord
from discord.ext import commands
from database import user_data, save_data  # 既存のデータベース周りに合わせてください

# 🕒 スパム防止のクールダウン管理用
cooldowns = {}

# 📊 レベルアップに必要な経験値の計算式（例: レベル × 100 XP）
def get_required_xp(level: int) -> int:
    return level * 100

# 👑 レベルに応じた付与ロールの設定（例: レベル5、レベル10など）
LEVEL_ROLES = {
    2: 1560621660585861170,
}

class ChatLevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1. ボット自身のメッセージやDMは無視
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        current_time = time.time()

        # 2. クールダウンチェック（60秒に1回のみ経験値獲得）
        if user_id in cooldowns and current_time - cooldowns[user_id] < 30:
            return

        # 3. リンク（URL）を正規表現で削除して、純粋なテキストの文字数を測る
        content = message.content
        url_pattern = re.compile(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+')
        clean_content = url_pattern.sub('', content).strip()

        char_count = len(clean_content)
        if char_count <= 0:
            return  # リンクだけ、または画像やスタンプだけで文字がない場合は経験値なし

        # クールダウンを更新
        cooldowns[user_id] = current_time

        # 4. 経験値の計算（1文字1xp、最大50xpでキャップ）
        earned_xp = min(50, char_count)

        # 5. ユーザーデータの取得・初期化
        if user_id not in user_data:
            user_data[user_id] = {}
        
        u_info = user_data[user_id]
        if "level" not in u_info:
            u_info["level"] = 1
        if "xp" not in u_info:
            u_info["xp"] = 0

        u_info["xp"] += earned_xp

        # 6. レベルアップ判定
        current_level = u_info["level"]
        required_xp = get_required_xp(current_level)

        if u_info["xp"] >= required_xp:
            u_info["xp"] -= required_xp
            u_info["level"] += 1
            new_level = u_info["level"]

            # お祝いメッセージを送信
            await message.channel.send(
                f"🎉 {message.author.mention} が **レベル {new_level}** にアップしました！"
            )

            # 7. 一定レベルに達したらロールを自動付与
            if new_level in LEVEL_ROLES:
                role_id = LEVEL_ROLES[new_level]
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await message.author.add_roles(role)
                        await message.channel.send(
                            f"✨ レベル報酬として {message.author.mention} にロール **{role.name}** を付与しました！"
                        )
                    except Exception as e:
                        print(f"ロール付与エラー: {e}")

        # データをセーブ
        save_data()

async def setup(bot):
    await bot.add_cog(ChatLevelSystem(bot))
