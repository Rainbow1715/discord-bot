# oc_data.py
from datetime import datetime
import pytz

# 🎂 うちの子データ一覧
OUR_CHILDREN = [
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
]

def get_today_birthday_children():
    """今日が誕生日のうちの子リストを返す"""
    jst = pytz.timezone('Asia/Tokyo')
    today_str = datetime.now(jst).strftime("%m-%d")
    
    return [child for child in OUR_CHILDREN if child.get("birthday") == today_str]
