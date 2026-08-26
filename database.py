import os
import json
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        print(f"❌ スプレッドシート接続エラー: {e}")
        return None

# スプレッドシートを取得
sheet = init_gspread()

# メモリ上のデータ保持用
user_data = {}

# --------------------------------------------------
# 🔰 初期キャラクターデータ（茉鈴・橘柊人・河野蜜柑）
# --------------------------------------------------
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

# --------------------------------------------------
# 📊 セーブデータの読み込みと保存（非同期対応）
# --------------------------------------------------
def load_data():
    global user_data
    if not sheet:
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

# 実際にスプレッドシートへ書き込む内部関数
def _sync_save():
    if not sheet:
        return
    try:
        rows = [["user_id", "data_json"]]
        for u_id, data in user_data.items():
            rows.append([str(u_id), json.dumps(data, ensure_ascii=False)])
        
        sheet.clear()
        sheet.update('A1', rows)
        print("💾 スプレッドシートへデータを保存しました。")
    except Exception as e:
        print(f"❌ データの保存エラー: {e}")

# Discordの返答を止めないようバックグラウンドで保存を実行
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
            "items": {"虹の欠片": 100, "ガチャチケ": 100},
            "characters": [dict(c) for c in DEFAULT_CHARACTERS],
            "party_indices": [0, 1, 2],
            "mails": []
        }
        save_data()

    u_info = user_data[user_id]

    # 既存ユーザーのキャラデータ補完
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
