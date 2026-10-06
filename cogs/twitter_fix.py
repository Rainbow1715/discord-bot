# cogs/twitter_fix.py
import re
import discord
from discord.ext import commands

# 🎯 対象にしたい特定のユーザーの Discord ユーザーID（数値）
TARGET_USER_IDS = [1221666245070557237]  # 👈 対象ユーザーのIDに変更してください

class TwitterFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # x.com または twitter.com のポストURLを検出する正規表現
        self.twitter_url_pattern = re.compile(
            r'https?://(?:www\.)?(?:x\.com|twitter\.com)/([a-zA-Z0-9_]+)/status/(\d+)'
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bot自身の発言は無視
        if message.author.bot:
            return

        # 特定のユーザー以外の発言は無視
        if message.author.id not in TARGET_USER_IDS:
            return

        # メッセージ内から Twitter/X のURLを検索
        matches = self.twitter_url_pattern.findall(message.content)
        if not matches:
            return

        # 検出されたすべてのTwitterリンクを変換
        converted_urls = []
        for username, tweet_id in matches:
            # fxtwitter.com に書き換えて末尾に /ja を付与
            fx_url = f"https://fxtwitter.com/{username}/status/{tweet_id}/ja"
            converted_urls.append(fx_url)

        if converted_urls:
            # 1. ユーザーの元メッセージの埋め込み（プレビュー）を非表示にする
            try:
                await message.edit(suppress_embeds=True)
            except discord.Forbidden:
                print("⚠️ [TwitterFix] メッセージ編集権限（埋め込みの抑制）が不足しています。")
            except Exception as e:
                print(f"⚠️ [TwitterFix] 埋め込み削除エラー: {e}")

            # 2. 変換後の fxtwitter リンクをリプライ送信
            reply_text = "\n".join(converted_urls)
            await message.reply(reply_text, mention_author=False)

async def setup(bot):
    await bot.add_cog(TwitterFix(bot))
