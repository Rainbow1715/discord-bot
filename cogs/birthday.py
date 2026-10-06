# cogs/birthday.py
import discord
from discord.ext import commands, tasks
from datetime import time, timezone, timedelta
from cogs import oc_data

JST = timezone(timedelta(hours=9))

# 📢 メッセージを送信したいDiscordチャンネルのID（ご自身のチャンネルIDに変更してください）
ANNOUNCE_CHANNEL_ID = 1368581096660402276  

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_check.start()  # タスク開始

    def cog_unload(self):
        self.birthday_check.cancel()  # タスク停止

    # 毎日 午前0:00 (JST) に自動判定して実行
    @tasks.loop(time=time(hour=0, minute=0, second=0, tzinfo=JST))
    async def birthday_check(self):
        await self.bot.wait_until_ready()
        
        channel = self.bot.get_channel(ANNOUNCE_CHANNEL_ID)
        if not channel:
            print("⚠️ [Birthday] 通知先のチャンネルが見つかりませんでした。")
            return

        today_children = oc_data.get_today_birthday_children()

        for child in today_children:
            name = child["name"]
            icon = child["icon"]
            address = child["address"]

            embed = discord.Embed(
                title="🎂 HAPPY BIRTHDAY!! 🎂",
                description=f"{icon} **今日は{name}の誕生日です！🎉**",
                color=0xFFB6C1  # ライトピンク
            )
            embed.add_field(name="🏠", value=address, inline=False)
            embed.set_footer(text="お誕生日おめでとうございます！")

            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Birthday(bot))
