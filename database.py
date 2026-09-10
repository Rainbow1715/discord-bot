print("🔍 database.py の読み込みを開始しました！")
import os
import json
import asyncio
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------
# 🌐 Google スプレッドシートの認証・接続設定
# --------------------------------------------------
def init_gspread():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    sheet_id = os.environ.get("SPREADSHEET_ID")
    
    if not creds_json or not sheet_id:
        print("⚠️ Google Credentials または SPREADSHEET_ID が設定されていません。")
        return None

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        worksheet = client.open_by_key(sheet_id).sheet1
        print("✅ Googleスプレッドシートへの接続に成功しました！")
        return worksheet
    except Exception as e:
        print(f"❌ スプレッドシート接続エラー: {e}")
        return None

sheet = init_gspread()
user_data = {}

# 🎰 レア度ごとの排出確率設定
RARITY_RATES = {
    "★5": 0.0000001,
    "★4": 0.12,
    "★3": 0.20,
    "★2": 0.35,
    "★1": 0.3499999,
}

# 🎂 今月のバースデー・ピックアップ設定
PICKUP_CHARACTERS = ["竹村しえら", "レオ", "Gerânio"]
PICKUP_BOOST_RATE = 0.40  # バースデーキャラ全体の排出補正率

# 🆕 新キャラ実装・ピックアップ設定
NEW_PICKUP_CHARACTERS = []  # 実装時に ["新キャラ名"] を指定
NEW_PICKUP_BOOST_RATE = 0.50 # 新キャラ全体の排出補正率

# 🎰 ガチャ排出キャラクタープール（兼マスターデータ）
GACHA_POOL = [
    {
        "name": "竹村しえら",
        "icon": "<:602506_siera:1524716095867719750>",
        "level": 1,
        "exp": 0,
        "rarity": "★3",
        "rate": 0.1,
        "hp": 90,
        "max_hp": 90,
        "atk": 22,
        "spd": 11,
        "rec": 6,
        "skill_name": "どけ！ 大天災しえらさんのお通りだぞ！",
        "skill_pow": 1.4,
        "element": "紫",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "女",
        "best_equip": "なんか強そうな棒",
        "equip": None,
        "likes": ["果肉なしいちごオレ"],
        "dislikes": ["激辛ラーメン", "紅茶"],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "れーちゃん",
        "icon": "<:602506_retyan:1476555773390618746>",
        "level": 1,
        "exp": 0,
        "rarity": "★4",
        "rate": 0.1,
        "hp": 100,
        "max_hp": 100,
        "atk": 25,
        "spd": 12,
        "rec": 18,
        "skill_name": "どけ！ おまいらの心を奪いにきたぞ！",
        "skill_pow": 1.1,
        "element": "光",
        "role": "アタッカー",
        "atk_type": "魔法",
        "gender": "？",
        "best_equip": "紙パックのいちごオレ",
        "equip": None,
        "likes": ["果肉なしいちごオレ"],
        "dislikes": ["激辛ラーメン", "紅茶"],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "レオ",
        "icon": "<:6005_reo:1476541458797559849>",
        "rarity": "★3",
        "count": 1,
        "level": 1,
        "exp": 0,
        "hp": 100,
        "max_hp": 100,
        "atk": 25,
        "spd": 16,
        "rec": 3,
        "skill_name": "ブッ殺してやる!",
        "skill_pow": 25,
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "ナイフ",
        "equip": None,
        "likes": ["クソデカステーキ"],
        "dislikes": ["野菜たっぷりサラダ", "ほうれん草のキッシュ", "ブロッコリー"],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "Gerânio",
        "icon": "<:602509_touwata:1524029854708662272>",
        "rarity": "★3",
        "rate": 0.2,
        "hp": 130,
        "max_hp": 130,
        "atk": 22,
        "spd": 17,
        "rec": 8,
        "skill_name": "一斉掃射",
        "skill_pow": 1.2,
        "element": "紫",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "ロケット",
        "equip": None,
        "likes": ["オムライス"],
        "dislikes": [],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "白黒レイ",
        "icon": "<:4_aituhanannnanda:1487097337556893827>",
        "rarity": "★5",
        "rate": 0.2,
        "hp": 17,
        "max_hp": 17,
        "atk": 17,
        "spd": 17,
        "rec": 5,
        "skill_name": "神だぞー",
        "skill_pow": 17,
        "element": "紫",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "？",
        "best_equip": "電子機器",
        "equip": None,
        "likes": ["果肉なしいちごオレ", "オムライス", "卵かけご飯"],
        "dislikes": ["納豆"],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "茉鈴",
        "icon": "<:6_marin:1476539399188648016>",
        "level": 1,
        "exp": 0,
        "hp": 80,
        "max_hp": 80,
        "atk": 5,
        "spd": 10,
        "rec": 20,
        "skill_name": "キラキラがたくさん！",
        "skill_pow": 1.2,
        "skill_type": "heal_all",
        "rarity": "★2",
        "count": 1,
        "element": "光",
        "role": "サポーター",
        "atk_type": "魔法",
        "gender": "女",
        "best_equip": "子供用カメラ",
        "equip": None,
        "likes": ["コーンマヨピザ", "オムライス"],
        "dislikes": ["激辛ラーメン"],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "橘柊人",
        "icon": "<:6_syuuto:1476538895968768000>",
        "level": 1,
        "exp": 0,
        "hp": 120,
        "max_hp": 120,
        "atk": 25,
        "spd": 12,
        "rec": 5,
        "skill_name": "ハリセン攻撃",
        "skill_pow": 1.5,
        "skill_type": "physical",
        "rarity": "★3",
        "count": 1,
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "ハリセン",
        "equip": None,
        "likes": [],
        "dislikes": ["酒"],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "河野蜜柑",
        "icon": "<:6_11_mikan:1539927243491385375>",
        "level": 1,
        "exp": 0,
        "hp": 90,
        "max_hp": 90,
        "atk": 10,
        "spd": 10,
        "rec": 8,
        "skill_name": "君たちにはこの虫が見えないの……？",
        "skill_pow": 1.0,
        "skill_type": "stun",
        "rarity": "★2",
        "count": 1,
        "element": "紫",
        "role": "サポーター",
        "atk_type": "魔法",
        "gender": "女",
        "best_equip": "学校の箒",
        "equip": None,
        "likes": [],
        "dislikes": [],
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    }
]

# --------------------------------------------------
# 🔰 初期キャラクターデータ取得関数
# --------------------------------------------------
def find_gacha_char(name):
    for c in GACHA_POOL:
        if c["name"] == name:
            return dict(c)  # 参照渡しを避けるためコピーを返す
    return None

DEFAULT_CHARACTERS = [
    find_gacha_char("茉鈴"),
    find_gacha_char("橘柊人"),
    find_gacha_char("河野蜜柑")
]

# 🍱 ご飯アイテムの定義
FOOD_ITEMS = {
    "ショートケーキ": {"icon": "🍰"},
    "激辛ラーメン": {"icon": "🍜"},
    "おにぎり": {"icon": "🍙"},
    "ハニーローストピーナッツ": {"icon": ""},
    "果肉なしいちごオレ": {"icon": ""},
    "紅茶": {"icon": ""},
    "クソデカステーキ": {"icon": ""},
    "野菜たっぷりサラダ": {"icon": ""},
    "酒": {"icon": ""},
    "オムライス": {"icon": ""},
    "卵かけご飯": {"icon": ""},
    "ブロッコリー": {"icon": ""},
    "納豆": {"icon": ""},
    "怪しい肉": {"icon": ""},
    "ほうれん草のキッシュ": {"icon": ""},
    "レモンのタルト": {"icon": ""},
    "コーンマヨピザ": {"icon": ""},
    "レモネード": {"icon": ""},
    "ナスの肉味噌炒め": {"icon": ""},
    "きのこのバター醤油炒め": {"icon": ""},
    "カプレーゼ": {"icon": ""},
    "バジルのスパゲッティ": {"icon": ""},
    "ラムネ": {"icon": ""},
    "ぶどうのコンポート": {"icon": ""},
    "ブルーベリージャムパン": {"icon": ""},
    "ピーマンの肉詰め": {"icon": ""},
}

# 📈 なつき度の必要経験値計算
def get_required_affection_exp(level):
    return level * 100

# 🎁 なつき度レベルアップ判定と報酬
def check_affection_level_up(char_data, user_info):
    rewards = []
    while True:
        req_exp = get_required_affection_exp(char_data["affection_level"])
        if char_data["affection_exp"] >= req_exp:
            char_data["affection_exp"] -= req_exp
            char_data["affection_level"] += 1
            lvl = char_data["affection_level"]
            
            if lvl % 5 == 0:
                rewards.append("🎫 ガチャチケ x1")
                user_info["items"]["ガチャチケ"] = user_info["items"].get("ガチャチケ", 0) + 1
            elif lvl % 3 == 0:
                rewards.append("💎 虹の欠片 x300")
                user_info["items"]["虹の欠片"] = user_info["items"].get("虹の欠片", 0) + 300
            else:
                rewards.append("🎁 ご飯ランダムボックス x1")
                user_info["items"]["ご飯ランダムボックス"] = user_info["items"].get("ご飯ランダムボックス", 0) + 1
        else:
            break
    return rewards

# --------------------------------------------------
# 🍺 お酒関連の設定
# --------------------------------------------------
ALCOHOL_ITEMS = ["酒", "ビール", "ワイン", "ウイスキー", "日本酒"]

ADULT_CHARACTERS = [
    "オリハラ カズヤ",
]

# 🍱 ご飯をあげる処理
def feed_character(user_info, char_data, food_name):
    char_name = char_data.get("name", "")

    if food_name in ALCOHOL_ITEMS and char_name not in ADULT_CHARACTERS:
        return {
            "status": "error",
            "reason": "underage_alcohol",
            "message": f"❌ **{char_name}** はお酒を飲むことができません！"
        }
        
    likes = char_data.get("likes", [])
    dislikes = char_data.get("dislikes", [])
    
    if "known_likes" not in char_data:
        char_data["known_likes"] = []
    if "known_dislikes" not in char_data:
        char_data["known_dislikes"] = []

    is_first_time = (food_name not in char_data["known_likes"]) and (food_name not in char_data["known_dislikes"])
    
    if food_name in likes:
        base_exp = 100
        taste_type = "like"
        if food_name not in char_data["known_likes"]:
            char_data["known_likes"].append(food_name)
    elif food_name in dislikes:
        base_exp = 20
        taste_type = "dislike"
        if food_name not in char_data["known_dislikes"]:
            char_data["known_dislikes"].append(food_name)
    else:
        base_exp = 50
        taste_type = "normal"

    first_bonus = 20 if is_first_time else 0
    total_gained_exp = base_exp + first_bonus

    char_data["affection_level"] = char_data.get("affection_level", 1)
    char_data["affection_exp"] = char_data.get("affection_exp", 0) + total_gained_exp

    rewards = check_affection_level_up(char_data, user_info)

    return {
        "taste_type": taste_type,
        "is_first_time": is_first_time,
        "gained_exp": total_gained_exp,
        "current_level": char_data["affection_level"],
        "rewards": rewards
    }

# --------------------------------------------------
# 📊 セーブデータの読み込みと保存（非同期対応）
# --------------------------------------------------
def load_data():
    global user_data
    if not sheet:
        print("⚠️ 【警告】sheetが初期化されていないため、読み込みをスキップしました。")
        return
    try:
        records = sheet.get_all_records()
        user_data.clear()
        for row in records:
            u_id = int(row["user_id"])
            user_data[u_id] = json.loads(row["data_json"])
        print("📊 スプレッドシートからデータを正常に読み込みました。")
    except Exception as e:
        print(f"❌ データの読み込みエラー: {e}")

def _sync_save():
    if not sheet:
        print("⚠️ 【警告】sheetが初期化されていないため、保存をスキップしました。")
        return
    try:
        rows = [["user_id", "data_json"]]
        for u_id, data in user_data.items():
            rows.append([str(u_id), json.dumps(data, ensure_ascii=False)])
        
        sheet.clear()
        sheet.update(range_name='A1', values=rows)
        print("💾 スプレッドシートへデータを保存しました。")
    except Exception as e:
        print(f"❌ データの保存エラー: {e}")

def save_data():
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _sync_save)
    except RuntimeError:
        _sync_save()

# 起動時に読み込み
load_data()

# --------------------------------------------------
# 👤 ユーザープロフィールの取得と補完
# --------------------------------------------------
def get_user_profile(user_id):
    user_id = int(user_id)
    if user_id not in user_data:
        user_data[user_id] = {
            "gold": 1000,
            "items": {"虹の欠片": 100, "ガチャチケ": 100, "おにぎり": 5, "ショートケーキ": 2, "激辛ラーメン": 2},
            "characters": [dict(c) for c in DEFAULT_CHARACTERS if c],
            "party_indices": [0, 1, 2],
            "mails": []
        }
        save_data()

    u_info = user_data[user_id]

    all_master_chars = {c["name"]: c for c in GACHA_POOL if c}

    for c in u_info.get("characters", []):
        char_name = c.get("name")
        master = all_master_chars.get(char_name, {})

        if master:
            c["element"] = master.get("element", c.get("element", "赤"))
            c["role"] = master.get("role", c.get("role", "アタッカー"))
            c["atk_type"] = master.get("atk_type", c.get("atk_type", "物理"))
            c["likes"] = master.get("likes", c.get("likes", []))
            c["dislikes"] = master.get("dislikes", c.get("dislikes", []))

        if "element" not in c:
            c["element"] = master.get("element", "赤")
        if "role" not in c:
            c["role"] = master.get("role", "アタッカー")
        if "atk_type" not in c:
            c["atk_type"] = master.get("atk_type", "物理")
        if "gender" not in c:
            c["gender"] = master.get("gender", "？")
        if "best_equip" not in c:
            c["best_equip"] = master.get("best_equip", None)
        if "equip" not in c:
            c["equip"] = None
        if "likes" not in c:
            c["likes"] = master.get("likes", [])
        if "dislikes" not in c:
            c["dislikes"] = master.get("dislikes", [])
        if "affection_level" not in c:
            c["affection_level"] = 1
        if "affection_exp" not in c:
            c["affection_exp"] = 0
        if "known_likes" not in c:
            c["known_likes"] = []
        if "known_dislikes" not in c:
            c["known_dislikes"] = []

    return u_info

# 起動時の保存テスト
save_data()
