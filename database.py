print("🔍 database.py の読み込みを開始しました！")
import os
import json
import asyncio
import gspread
from google.oauth2.service_account import Credentials
import copy

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
    "★2": 0.33,
    "★1": 0.3499999,
}

# 🎂 今月のバースデー・ピックアップ設定
PICKUP_CHARACTERS = ["竹村しえら", "レオ", "Gerânio"]
PICKUP_BOOST_RATE = 0.40  # バースデーキャラ全体の排出補正率

# 🆕 新キャラ実装・ピックアップ設定
NEW_PICKUP_CHARACTERS = ["ロイ", "折原和也", "神明龍矢"]  # 実装時に ["新キャラ名"] を指定
NEW_PICKUP_BOOST_RATE = 0.50 # 新キャラ全体の排出補正率

# 🎰 ガチャ排出キャラクタープール（兼マスターデータ）
GACHA_POOL = [
    {
        "name": "竹村しえら",
        "icon": "<:602506_siera:1524716095867719750>",
        "level": 1,
        "exp": 0,
        "rarity": "★3",
        "hp": 90,
        "max_hp": 90,
        "atk": 22,
        "spd": 11,
        "rec": 6,
        "skill_name": "どけ！ 大天災しえらさんのお通りだぞ！",
        "skill_type": "physical",
        "skill_pow": 16,
        "element": "紫",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "女",
        "best_equip": "なんか強そうな棒",
        "equip": None,
        "likes": {
            "果肉なしいちごオレ": "やっぱりいちごオレは果肉なしに限るな！ と上機嫌で飲んでいた。",
        },
        "dislikes": {
            "激辛ラーメン": "涙目になりながらもしっかりと完食していた。",
            "紅茶": "渋い顔で、しばらくカップと睨めっこをしていた。",
        },
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": [],
    },
    {
        "name": "れーちゃん",
        "icon": "<:602506_retyan:1476555773390618746>",
        "level": 1,
        "exp": 0,
        "rarity": "★4",
        "hp": 100,
        "max_hp": 100,
        "atk": 25,
        "spd": 12,
        "rec": 18,
        "skill_name": "どけ！ おまいらの心を奪いにきたぞ！",
        "skill_pow": 26,
        "element": "光",
        "role": "アタッカー",
        "atk_type": "魔法",
        "gender": "？",
        "best_equip": "紙パックのいちごオレ",
        "equip": None,
        "likes": {
            "果肉なしいちごオレ": "このねぇ、じんこー的ないちごの味がいいんですよねこれ、などぶつぶつ言っていた。",
        },
        "dislikes": {
            "激辛ラーメン": "食べる前にまず水を要求してきた。",
            "紅茶": "うーん、れーちゃんこれいらないや……、とあからさまにテンションを下げつつ言ってきた。",
        },
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "レオ",
        "icon": "<:6005_reo:1476541458797559849>",
        "rarity": "★3",
        "level": 1,
        "exp": 0,
        "hp": 100,
        "max_hp": 100,
        "atk": 25,
        "spd": 16,
        "rec": 3,
        "skill_name": "ブッ殺してやる!",
        "skill_type": "physical",
        "skill_pow": 25,
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "ナイフ",
        "equip": None,
        "likes": {
            "クソデカステーキ": "大喜びでがっついて食べた。",
        },
        "dislikes": { 
            "野菜たっぷりサラダ": "いらない、と突き返してきた。",
            "ほうれん草のキッシュ": "嫌そうな顔をしていた。",
            "ブロッコリー": "いらないと言っていたが、サラもブロッコリーが嫌いだ、と言うと余裕の笑みを浮かべて食べた。",
        },
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "Gerânio",
        "icon": "<:602509_touwata:1524029854708662272>",
        "rarity": "★3",
        "hp": 130,
        "max_hp": 130,
        "atk": 22,
        "spd": 17,
        "rec": 8,
        "skill_name": "一斉掃射",
        "skill_type": "physical",
        "skill_pow": 18,
        "element": "紫",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "ロケット",
        "equip": None,
        "likes": {
            "オムライス": "妻が作ってくれたものと似ている、と少し嬉しそうに食べていた。"
        },
        "dislikes": {},
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "白黒レイ",
        "icon": "<:4_aituhanannnanda:1487097337556893827>",
        "rarity": "★5",
        "hp": 170,
        "max_hp": 170,
        "atk": 170,
        "spd": 170,
        "rec": 17,
        "skill_name": "神だぞー",
        "skill_pow": 17,
        "element": "紫",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "？",
        "best_equip": "電子機器",
        "equip": None,
        "likes": {
            "果肉なしいちごオレ": "果肉なんていらんねん。人工的なこの味わいをごくごくしたいのですよ。",
            "オムライス": "実はケチャップライスとかケチャップとか、そんなに好きじゃないよ",
            "卵かけご飯": "たまに白身でうえっってなることない？（炎上）",
            "塩": "角砂糖のノリの塩は美味しくないのでオススメしません",
        },
        "dislikes": {
            "納豆": "くっっっっせぇ！！！！！！！！！！！！（炎上）",
        },
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
        "skill_pow": 12,
        "skill_type": "heal_all",
        "rarity": "★2",
        "element": "光",
        "role": "サポーター",
        "atk_type": "魔法",
        "gender": "女",
        "best_equip": "子供用カメラ",
        "equip": None,
        "likes": {
            "コーンマヨピザ": "これおいしいねぇ！ と口いっぱいに頬張っていた。",
            "オムライス": "口の周りをケチャップで汚しながら美味しそうに食べていた。",
        },
        "dislikes": {
            "激辛ラーメン": "一口食べて泣きそうな顔になっていた。",
        },
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
        "skill_pow": 19,
        "skill_type": "physical",
        "rarity": "★3",
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "ハリセン",
        "equip": None,
        "likes": {},
        "dislikes": {
            "酒": "何か恨みでもあるのか、ずっと睨んでいた。",
        },
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
        "skill_pow": 13,
        "skill_type": "stun",
        "rarity": "★2",
        "element": "紫",
        "role": "サポーター",
        "atk_type": "魔法",
        "gender": "女",
        "best_equip": "学校の箒",
        "equip": None,
        "likes": {
            "ピーマンの肉詰め": "少し笑顔になり、美味しそうに静かにもぐもぐしていた。",
        },
        "dislikes": {},
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "ロイ",
        "icon": "<:6006_roi:1476541556227047504>",
        "rarity": "★3",
        "hp": 95,
        "max_hp": 95,
        "atk": 22,
        "spd": 18,
        "rec": 8,
        "skill_name": "うっふ〜ん♡激エロお兄さんだよ〜♡",
        "skill_type": "charm",
        "charm_target": "女",
        "skill_trigger": "interval_3",
        "skill_rate": 95,
        "element": "赤",
        "role": "サポーター",
        "atk_type": "魔法",
        "gender": "男",
        "best_equip": "鏡",
        "equip": None,
        "likes": {
            "ブルーベリージャムパン": "ジャムを大量に塗りたくってやったのに、手も口元も汚さず完食しやがった。"
        },
        "dislikes": {
            "クソデカステーキ": "普通のサイズのはないの？　と文句を言ってきた。"
        },
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "折原和也",
        "icon": "<:602602_orihara:1476550258627444747>",
        "rarity": "★3",
        "hp": 82,
        "max_hp": 82,
        "atk": 14,
        "spd": 15,
        "rec": 4,
        "skill_name": "モルモットとの戯れ",
        "skill_type": "buff_all_atk",
        "skill_pow": 0.20,
        "skill_trigger": "interval_3",
        "skill_rate": 100,
        "element": "青",
        "role": "アタッカー",
        "atk_type": "物理",
        "gender": "男",
        "best_equip": "怪しい試験管",
        "equip": None,
        "likes": {
            "紅茶": "偶然遊びに来ていた茉鈴に、怪しい錠剤を入れて飲ませようとしたので慌てて止めた。"
        },
        "dislikes": {
            "酒": "研究が鈍るじゃないか、と怒ってきた。"
        },
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "神明龍矢",             # [文字列] キャラクター名
        "icon": "<:602606_tatuya:1517868436951273513>",             # [文字列] アイコンデータ（Discord絵文字IDなど）
        "gender": "男",           # [文字列] 性別（"男", "女", "？"）
        "rarity": "★3",           # [文字列] レアリティ（"★2" 〜 "★5"）
        "element": "赤",         # [文字列] 属性（"赤", "青", "紫", "光" など）
        "role": "アタッカー",            # [文字列] 戦闘での役割（"アタッカー", "サポーター"）
        "atk_type": "物理",        # [文字列] 攻撃タイプ（"物理", "魔法"）
        # --- ステータス・成長 ---
        "level": 1,           # [数値] 現在のレベル
        "exp": 0,             # [数値] 現在の獲得経験値
        "hp": 98,               # [数値] 現在のHP
        "max_hp": 98,           # [数値] 最大HP
        "atk": 30,             # [数値] 攻撃力
        "spd": 20,             # [数値] 素早さ（行動順）
        "rec": 10,             # [数値] 回復力（回復スキル等の効果量）
        # --- スキル関連 ---
        "skill_name": "黙って人の言うこと聞けねぇ奴は、背中刺されて死んだらいい。",      # [文字列] スキル名
        "skill_type": "physical",      # [文字列] スキルの効果種別（"physical", "heal_all", "stun", "charm", "buff_all_atk" など）
        "skill_pow": 20,       # [数値] スキル威力・倍率
        "skill_trigger": "chance",   # [文字列] 発動条件（例: "interval_3" = 3ターン毎）※一部キャラのみ
        "skill_rate": 75,      # [数値] 発動成功率(%)（例: 95 = 95%）※一部キャラのみ
        # --- 装備関連 ---
        "best_equip": "酒瓶",      # [文字列] 相性の良いモチーフ装備名
        "equip": None,           # [None / 辞書] 現在装備中のアイテムデータ
        # --- 好感度・交流システム ---
        "likes": {
            "酒": "龍矢は出された酒を上機嫌で飲み干した。",   # [辞書] 好きな食べ物とリアクション文 {"アイテム名": "テキスト"}
        },
        "dislikes": {
            "カプレーゼ": "気取った横文字の食べ物なんざ出してくるな、とブチ切れた。",
        },                                        # [辞書] 嫌いな食べ物とリアクション文 {"アイテム名": "テキスト"}
        "affection_level": 1,  # [数値] 現在の好感度レベル
        "affection_exp": 0,    # [数値] 現在の好感度経験値
        "known_likes": [],      # [リスト] 発見済みの「好きなもの」リスト
        "known_dislikes": [],   # [リスト] 発見済みの「嫌いなもの」リスト
    }
]

# --------------------------------------------------
# 🔰 初期キャラクターデータ取得関数
# --------------------------------------------------
def find_gacha_char(name):
    for c in GACHA_POOL:
        if c["name"] == name:
            return copy.deepcopy(c)  # 参照渡しを避けるためコピーを返す
    return None

DEFAULT_CHARACTERS = [
    find_gacha_char("茉鈴"),
    find_gacha_char("橘柊人"),
    find_gacha_char("河野蜜柑")
]

# 装備！！！！！
EQUIPMENT_GACHA_POOL = {
    "name": "鉄の剣", "rarity": 3, "icon": "🗡️", "atk_bonus": 15, "hp_bonus": 0, "desc": "一般的な鉄製の剣。"},

EQUIPMENT_GACHA_POOL = {
    "なんか強そうな棒": {"icon": ""},
    "紙パックのいちごオレ": {"icon": ""},
    "ナイフ": {"icon": ""},
    "ロケット": {"icon": ""},
    "電子機器": {"icon": ""},
    "子供用カメラ": {"icon": ""},
    "ハリセン": {"icon": ""},
    "学校の箒": {"icon": ""},
    



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
    "塩": {"icon": ""},
    "プロテインラーメン": {"icon": ""},
}

# 📈 なつき度の必要経験値計算
def get_required_affection_exp(level):
    return level * 100

# 🎁 なつき度レベルアップ判定と報酬（上限30レベル設定・経験値ストック対応）
def check_affection_level_up(char_data, user_info):
    rewards = []
    MAX_AFFECTION_LEVEL = 30  # 👈 なつき度の上限レベル

    while True:
        # すでに上限レベルに達している場合はレベルアップを行わず、経験値をそのままストックする
        if char_data["affection_level"] >= MAX_AFFECTION_LEVEL:
            char_data["affection_level"] = MAX_AFFECTION_LEVEL
            break

        req_exp = get_required_affection_exp(char_data["affection_level"])
        if char_data["affection_exp"] >= req_exp:
            char_data["affection_exp"] -= req_exp
            char_data["affection_level"] += 1
            lvl = char_data["affection_level"]
            
            # 報酬の付与判定
            if lvl % 5 == 0:
                rewards.append("🎫 ガチャチケ x1")
                user_info["items"]["ガチャチケ"] = user_info["items"].get("ガチャチケ", 0) + 1
            elif lvl % 3 == 0:
                rewards.append("💎 虹の欠片 x300")
                user_info["items"]["虹の欠片"] = user_info["items"].get("虹の欠片", 0) + 300
            else:
                rewards.append("🎁 ランダムご飯ボックス x1")
                user_info["items"]["ランダムご飯ボックス"] = user_info["items"].get("ランダムご飯ボックス", 0) + 1
        else:
            break

    return rewards

# --------------------------------------------------
# 🍺 お酒関連の設定
# --------------------------------------------------
ALCOHOL_ITEMS = ["酒", "ビール", "ワイン", "ウイスキー", "日本酒"]

ADULT_CHARACTERS = [
    "折原和也", "橘柊人", "竹村しえら", "れーちゃん", "Gerânio", "レオ", "ロイ", "白黒レイ", "神明龍矢",
]

# --------------------------------------------------
# 🍖 怪しい肉関連の設定
# --------------------------------------------------
SUSPICIOUS_MEAT_ITEMS = ["怪しい肉"]

SUSPICIOUS_MEAT_CHARACTERS = [
    "Branch Coral", "Root Coral",
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

    # 「怪しい肉」をあげる時の処理イメージ
    if food_name in SUSPICIOUS_MEAT_ITEMS and char_name not in SUSPICIOUS_MEAT_CHARACTERS:
        return {
            "status": "error",
            "reason": "refused",
            "message": f"❌ **{char_name}** にこんなものあげようとしないでください！"
        }
        
    # GACHA_POOL から最新のマスターデータを取得
    master_char = find_gacha_char(char_name) or {}
    master_likes = master_char.get("likes", {})
    master_dislikes = master_char.get("dislikes", {})

    if "known_likes" not in char_data:
        char_data["known_likes"] = []
    if "known_dislikes" not in char_data:
        char_data["known_dislikes"] = []

    # ⭕️ 食べたことのある全履歴リストを初期化
    if "eaten_foods" not in char_data:
        char_data["eaten_foods"] = []

    # ⭕️ 「一度でも食べたことがあるか」で初めて判定を行う
    is_first_time = food_name not in char_data["eaten_foods"]

    # ⭕️ 食べた履歴に保存（これで次回以降は False になる）
    if is_first_time:
        char_data["eaten_foods"].append(food_name)
    
    # 辞書・リストのどちらの形式でも安全に判定
    is_like = food_name in master_likes
    is_dislike = food_name in master_dislikes

    if is_like:
        base_exp = 100
        taste_type = "like"
        if food_name not in char_data["known_likes"]:
            char_data["known_likes"].append(food_name)
    elif is_dislike:
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
            "items": {"虹の欠片": 100, "ガチャチケ": 100, "装備ガチャチケット": 10, "おにぎり": 5, "ショートケーキ": 2, "激辛ラーメン": 2},
            "characters": [copy.deepcopy(c) for c in DEFAULT_CHARACTERS if c],
            "equipments": [],
            "party_indices": [0, 1, 2],
            "mails": []
        }
        save_data()

    u_info = user_data[user_id]

    # ★既存ユーザー向けのデータ補完処理（データが無い場合に自動追加）
    items = u_info.setdefault("items", {})
    if "装備ガチャチケット" not in items:
        items["装備ガチャチケット"] = 0  # ★追記：未所持なら0枚で初期化

    if "equipments" not in u_info:
        u_info["equipments"] = []  # ★追記：未作成なら空リストで初期化

    all_master_chars = {c["name"]: c for c in GACHA_POOL if c}

    for c in u_info.get("characters", []):
        char_name = c.get("name")
        master = all_master_chars.get(char_name, {})

        if master:
            c["element"] = master.get("element", c.get("element", "赤"))
            c["role"] = master.get("role", c.get("role", "アタッカー"))
            c["atk_type"] = master.get("atk_type", c.get("atk_type", "物理"))
            c["likes"] = master.get("likes", c.get("likes", {}))
            c["dislikes"] = master.get("dislikes", c.get("dislikes", {}))

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
            c["likes"] = master.get("likes", {})
        if "dislikes" not in c:
            c["dislikes"] = master.get("dislikes", {})
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
