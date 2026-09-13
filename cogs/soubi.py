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

        # 装備！！！！！
        # EQUIPMENT_GACHA_POOL = {
        #     "name": "鉄の剣", "rarity": 3, "icon": "🗡️", "atk_bonus": 15, "hp_bonus": 0, "desc": "一般的な鉄製の剣。"},

    "なんか強そうな棒": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "その辺に落ちてそうな棒。強いのか？"
    },
    "紙パックのいちごオレ": {
        "icon": "",
        "rarity": 4,
        "p_hp": 100,
        "description": "美味しい。毎ターンHP100回復。"
    },
    "ナイフ": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "普通のナイフ。"
    },
    "ロケット": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "中に女性の写真が入っている。"
    },
    "電子機器": {
        "icon": "",
        "rarity": 5,
        "atk": 500,
        "description": "ばか"
    },
    "子供用カメラ": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "一応撮れる。"
    },
    "ハリセン": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "いい音が鳴りそう。"
    },
    "学校の箒": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "掃除でもするんですか？"
    },
    "鏡": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "この世で1番美しいのはだぁれ？"
    },
    "怪しい試験管": {
        "icon": "",
        "rarity": 3,
        "p_hp": 50,
        "description": "何が入ってるんですかこれ"
    },
    "酒瓶": {
        "icon": "",
        "rarity": 3,
        "atk": 10,
        "description": "割れると痛いですよ。"
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
