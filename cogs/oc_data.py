# oc_data.py
from datetime import datetime
import pytz

# 🎂 うちの子データ一覧
OUR_CHILDREN = [
    {
        "name": "テスト",
        "icon": "<:4_aituhanannnanda:1487097337556893827>",
        "birthday": "10-6",
        "address": "　",
    },
    {
        "name": "清藤弦也",
        "icon": "<:6_32_genya:1539928472787623987>",
        "birthday": "01-09",
        "address": "HKK施設"
    },
    {
        "name": "橘柊人",
        "icon": "<:6_syuuto:1476538895968768000>",
        "birthday": "11-01",
        "address": "卓"
    },
    {
        "name": "神明彼方",
        "icon": "<:602505_kanata:1507520855150694451>",
        "birthday": "3-19",
        "address": "呪福",
    },
    {
        "name": "神明彰",
        "icon": "<:602605_teru:1507520727404773386>",
        "birthday": "4-13",
        "address": "呪福",
    },
    {
        "name": "須藤雷",
        "icon": "<:602508_sudou:1524029760492142592>",
        "birthday": "6-6",
        "address": "呪福",
    },
    {
        "name": "竹村しえら",
        "icon": "<:602506_siera:1524716095867719750>",
        "birthday": "8-3",
        "address": "呪福",
    },
    {
        "name": "戸叶茜哉",
        "icon": "<:602607_sennya:1526163946669871134>",
        "birthday": "5-9",
        "address": "呪福",
    },
    {
        "name": "Branch Coral",
        "icon": "<:602511_branch:1476555662438699089>",
        "birthday": "11-8",
        "address": "呪福",
    },
    {
        "name": "Root Coral",
        "icon": "<:602601_sango:1524029917279555737>",
        "birthday": "11-8",
        "address": "呪福",
    },
    {
        "name": "Gerânio",
        "icon": "<:602509_touwata:1524029854708662272>",
        "birthday": "8-29",
        "address": "呪福",
    },
    {
        "name": "鶴谷大空",
        "icon": "<:602609_turuyasora:1549595028555304990>",
        "birthday": "9-21",
        "address": "呪福",
    },
    {
        "name": "竜胆廉",
        "icon": "<:602512_rindouren:1476548499662442516>",
        "birthday": "3-24",
        "address": "断罪",
    },
    {
        "name": "レオ",
        "icon": "<:6005_reo:1476541458797559849>",
        "birthday": "8-13",
        "address": "　",
    },
    {
        "name": "ロイ",
        "icon": "<:6006_roi:1476541556227047504>",
        "birthday": "9-24",
        "address": "　",
    },
    {
        "name": "アリア",
        "icon": "<:6011_aria:1476541480523927654>",
        "birthday": "2-10",
        "address": "　",
    },
    {
        "name": "サラ",
        "icon": "<:6002_sara:1491351595290722314>",
        "birthday": "5-2",
        "address": "　",
    },
    {
        "name": "茉鈴",
        "icon": "<:6_marin:1476539399188648016>",
        "birthday": "4-16",
        "address": "創作",
    },
]

def get_today_birthday_children():
    """今日が誕生日のうちの子リストを返す"""
    jst = pytz.timezone('Asia/Tokyo')
    today_str = datetime.now(jst).strftime("%m-%d")
    
    return [child for child in OUR_CHILDREN if child.get("birthday") == today_str]
