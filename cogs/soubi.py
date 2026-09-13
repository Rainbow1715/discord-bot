import discord
from discord.ext import commands

# 🗡️ 装備データはすべてここにまとめる！
EQUIPMENT_MASTER = {
    "鉄の剣": {
        "icon": "⚔️",
        "rarity": 3,
        "atk": 10,
        "description": "一般的な鉄製の剣。"
    },
    "鋼の剣": {
        "icon": "⚔️",
        "rarity": 4,
        "atk": 25,
        "description": "鍛え抜かれた鋼の剣。"
    },
    "聖剣エクスカリバー": {
        "icon": "🗡️",
        "rarity": 5,
        "atk": 60,
        "description": "伝説の聖剣。"
    },
}

class SoubiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="装備ガチャ")
    async def open_soubi_gacha(self, ctx):
        from gacha import SoubiGachaView
        view = SoubiGachaView(ctx.author.id)
        await ctx.send("🗡️ 装備ガチャ", view=view)

async def setup(bot):
    await bot.add_cog(SoubiCog(bot))
