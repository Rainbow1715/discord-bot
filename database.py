import json
import os

DATA_FILE = "user_data.json"

# 🔰 初期キャラクターデータ
DEFAULT_CHARACTERS = [
    {
        "name": "茉鈴",
        "level": 1,
        "exp": 0,
        "hp": 100,
        "max_hp": 100,
        "atk": 15,
        "spd": 10,
        "rec": 20,
        "skill_name": "キラキラがたくさん！",
        "skill_pow": 1.2,
        "skill_type": "heal_all",
        "rarity": "★3",
        "count": 1,
        "element": "光",
        "role": "サポーター",
        "gender": "女",
        "best_equip": "子供用カメラ",
        "equip": None
    },
    {
        "name": "橘柊人",
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
        "gender": "男",
        "best_equip": "ハリセン",
        "equip": None
    },
    {
        "name": "河野蜜柑",
        "level": 1,
        "exp": 0,
        "hp": 90,
        "max_hp": 90,
        "atk": 20,
        "spd": 15,
        "rec": 8,
        "skill_name": "君たちにはこの虫が見えないの……？",
        "skill_pow": 1.0,
        "skill_type": "stun",
        "rarity": "★3",
        "count": 1,
        "element": "紫",
        "role": "サポーター",
        "gender": "女",
        "best_equip": "学校の箒",
        "equip": None
    }
]

# 🎰 ガチャ排出キャラクタープール
GACHA_POOL = [
    {
        "name": "アルク",
        "rarity": "★3",
        "rate": 0.1,
        "hp": 110,
        "max_hp": 110,
        "atk": 22,
        "spd": 11,
        "rec": 6,
        "skill_name": "スラッシュ",
        "skill_pow": 1.4,
        "element": "赤",
        "role": "アタッカー",
        "gender": "男",
        "best_equip": None,
        "equip": None
    },
    {
        "name": "リリィ",
        "rarity": "★3",
        "rate": 0.1,
        "hp": 95,
        "max_hp": 95,
        "atk": 14,
        "spd": 12,
        "rec": 18,
        "skill_name": "ヒールシャワー",
        "skill_pow": 1.1,
        "element": "青",
        "role": "サポーター",
        "gender": "女",
        "best_equip": None,
        "equip": None
    },
    {
        "name": "ボルト",
        "rarity": "★3",
        "rate": 0.1,
        "hp": 140,
        "max_hp": 140,
        "atk": 18,
        "spd": 8,
        "rec": 4,
        "skill_name": "シールドバッシュ",
        "skill_pow": 1.2,
        "element": "緑",
        "role": "ディフェンダー",
        "gender": "男",
        "best_equip": None,
        "equip": None
    },
    {
        "name": "シエル",
        "rarity": "★2",
        "rate": 0.2,
        "hp": 85,
        "max_hp": 85,
        "atk": 16,
        "spd": 14,
        "rec": 8,
        "skill_name": "ウィンドアロー",
        "skill_pow": 1.2,
        "element": "緑",
        "role": "アタッカー",
        "gender": "女",
        "best_equip": None,
        "equip": None
    },
    {
        "name": "カグラ",
        "rarity": "★2",
        "rate": 0.2,
        "hp": 100,
        "max_hp": 100,
        "atk": 20,
        "spd": 10,
        "rec": 5,
        "skill_name": "焔一閃",
        "skill_pow": 1.3,
        "element": "赤",
        "role": "アタッカー",
        "gender": "女",
        "best_equip": None,
        "equip": None
    },
    {
        "name": "ゼファー",
        "rarity": "★2",
        "rate": 0.3,
        "hp": 80,
        "max_hp": 80,
        "atk": 15,
        "spd": 16,
        "rec": 6,
        "skill_name": "疾風連撃",
        "skill_pow": 1.1,
        "element": "青",
        "role": "アタッカー",
        "gender": "男",
        "best_equip": None,
        "equip": None
    }
]

# セーブデータの読み込み
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

user_data = load_data()

# セーブデータの保存
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

# ユーザープロフィールの取得とデータ補完
def get_user_profile(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "gold": 1000,
            "items": {"虹の欠片": 100, "ガチャチケ": 100},
            "characters": [dict(c) for c in DEFAULT_CHARACTERS],
            "party_indices": [0, 1, 2],
            "mails": []
        }
        save_data()

    u_info = user_data[user_id]

    # 既存ユーザーのキャラデータ補完（項目がない場合のみ追加）
    for c in u_info.get("characters", []):
        if "element" not in c:
            c["element"] = "赤"
        if "role" not in c:
            c["role"] = "アタッカー"
        if "gender" not in c:
            c["gender"] = "？"
        if "best_equip" not in c:
            c["best_equip"] = None
        if "equip" not in c:
            c["equip"] = None

    return u_info
