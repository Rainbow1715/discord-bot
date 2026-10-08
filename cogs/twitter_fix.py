# cogs/twitter_fix.py
import asyncio
import re
import discord
from discord.ext import commands

# 🎯 対象にしたい特定のユーザーの Discord ユーザーID（数値）
TARGET_USER_IDS = [1221666245070557237]


class TwitterFix(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # x.com または twitter.com のポストURLを検出する正規表現
        self.twitter_url_pattern = re.compile(
            r"https?://(?:www\.)?(?:x\.com|twitter\.com)/([a-zA-Z0-9_]+)/status/(\d+)"
        )

    async def process_twitter_link(
        self, message: discord.Message, is_edit: bool = False
    ):
        """リンク判定・埋め込み非表示・リプライの共通処理"""
        # Bot自身の発言や特定ユーザー以外は無視
        if message.author.bot or message.author.id not in TARGET_USER_IDS:
            return

        matches = self.twitter_url_pattern.findall(message.content)
        if not matches:
            return

        # 編集イベント（Discordが後から埋め込みを追加した時）の場合
        if is_edit:
            try:
                if message.embeds:
                    await message.edit(suppress=True)
            except Exception:
                pass
            return

        # 1. 変換後の fxtwitter リンクを作成
        converted_urls = [
            f"https://fxtwitter.com/{username}/status/{tweet_id}/ja"
            for username, tweet_id in matches
        ]

        # 2. 少しだけ待ってDiscord側に埋め込みを生成させる（1秒）
        await asyncio.sleep(1.0)

        # 3. ユーザーの元メッセージの埋め込み（プレビュー）を非表示にする
        try:
            await message.edit(suppress=True)
        except discord.Forbidden:
            print(
                "⚠️ [TwitterFix] メッセージ編集権限（メッセージの管理）が不足しています。"
            )
        except Exception as e:
            print(f"⚠️ [TwitterFix] 埋め込み削除エラー: {e}")

        # 4. 変換後の fxtwitter リンクをリプライ送信
        reply_text = "\n".join(converted_urls)
        await message.reply(reply_text, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """新規メッセージ受信時"""
        await self.process_twitter_link(message, is_edit=False)

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ):
        """Discordが後から埋め込みを追加・更新した時"""
        await self.process_twitter_link(after, is_edit=True)


async def setup(bot):
    await bot.add_cog(TwitterFix(bot))
