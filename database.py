print("🔍 database.py の読み込みを開始しました！")
import os
import json
import asyncio
import gspread
from google.oauth2.service_account import Credentials
import copy
import os
import importlib.util

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
PICKUP_CHARACTERS = []
PICKUP_BOOST_RATE = 0.60  # バースデーキャラ全体の排出補正率

# 🆕 新キャラ実装・ピックアップ設定
NEW_PICKUP_CHARACTERS = ["レオ(仮面ライダーパロ)", "ムクロ(トリッカルパロ)", "しえら(仮面ライダーパロ)", "ルシア(トリッカルパロ)",]
NEW_PICKUP_BOOST_RATE = 0.50

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
            "オムライス": "妻が作ってくれたものと似ている、と少し嬉しそうに食べていた。",
            "おにぎり": "懐かしい味ですね、と少し微笑みながら食べていた。"
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
            "オムライス": "口の周りをケチャップで汚しながら美味しそうに食べていていた。",
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
            "クソデカステーキ": "普通のサイズのはないの？ と文句を言ってきた。",
        },
        "special_reactions": {"怪しい肉": "え……何これ？ と顔を顰めていた。食べたことはなさそうだった。"},
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
            "酒": "研究が鈍るじゃないか、と怒ってきた。",
        },
        "special_reactions": {"怪しい肉": "……元はどのモルモットだい？ と聞いてきた。食べたことはなさそうだった。"},
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "神明龍矢",
        "icon": "<:602606_tatuya:1517868436951273513>",
        "gender": "男",
        "rarity": "★3",
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "level": 1,
        "exp": 0,
        "hp": 98,
        "max_hp": 98,
        "atk": 30,
        "spd": 20,
        "rec": 10,
        "skill_name": "黙って人の言うこと聞けねぇ奴は、背中刺されて死んだらいい。",
        "skill_type": "child_slayer",
        "skill_pow": 50,
        "skill_trigger": "chance",
        "skill_rate": 75,
        "best_equip": "酒瓶",
        "equip": None,
        "likes": {
            "酒": "龍矢は出された酒を上機嫌で飲み干した。",
        },
        "dislikes": {
            "カプレーゼ": "気取った横文字の食べ物なんざ出してくるな、とブチ切れた。",
        },
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": []
    },
    {
        "name": "サラ", 
        "icon": "<:6002_sara:1491351595290722314>", 
        "gender": "男", 
        "rarity": "★3", 
        "element": "緑", 
        "role": "ディフェンダー", 
        "atk_type": "物理", 
        "level": 1, 
        "exp": 0, 
        "hp": 200, 
        "max_hp": 200, 
        "atk": 9, 
        "spd": 22, 
        "rec": 15, 
        "skill_name": "うわああああああああこっちこないで！！！！！", 
        "skill_type": "multi_hit", 
        "skill_trigger": "chance", 
        "skill_rate": 20, 
        "best_equip": "片手剣", 
        "equip": None, 
        "likes": {
            "レモンのタルト": "美味しそうにボロボロこぼしながら食べた。",
            "コーンマヨピザ": "ジャンキーなもの好きなんですよねぇ、と言いながら頬張っていた。",
            "レモネード": "少し酸っぱそうだった。",
        },
        "dislikes": {
            "ブロッコリー": "サラの前に茹どもしていない生のブロッコリーを出した。サラは正気を疑ってきた。",
            "ナスの肉味噌炒め": "騙されないぞ！ これナス入ってますよね？！ と言って逃げた。",
            "きのこのバター醤油炒め": "どう見てもきのこ入ってるじゃないですかやだ-っ！！ と喚いて逃げた。",
            "カプレーゼ": "……………どう見てもトマトじゃないですかこれ。と言われた。サラはこれを食べなかった。",
            "ピーマンの肉詰め": "これを出すとサラは渋い顔をした。レオでも食べれるぞ、と言っても だから何なんですか？ と言って残した。",
        },
        "special_reactions": {"怪しい肉": "すんすんと匂いを嗅ぎ、露骨に嫌そうな顔をした。食べたことはなさそうだった。"},
        "affection_level": 1, 
        "affection_exp": 0, 
        "known_likes": [], 
        "known_dislikes": [], 
    },
    {
        "name": "しえら(猫)",
        "icon": "<:701_siera:1549700587145269269>",
        "gender": "女", 
        "rarity": "★1", 
        "element": "青", 
        "role": "アタッカー", 
        "atk_type": "物理", 
        "level": 1,
        "exp": 0,
        "hp": 45, 
        "max_hp": 45, 
        "atk": 11, 
        "spd": 6, 
        "rec": 3,
        "skill_name": "引っ掻く", 
        "skill_type": "physical", 
        "skill_pow": 0.8, 
        "skill_trigger": "chance", 
        "skill_rate": 60,
        "best_equip": "", 
        "equip": None,
        "likes": {}, 
        "dislikes": {}, 
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": [],
    },
    {
        "name": "彼方(狐)",
        "icon": "<:702_kanata:1549702062261018694>",
        "gender": "男", 
        "rarity": "★1", 
        "element": "緑", 
        "role": "ディフェンダー", 
        "atk_type": "物理",
        "level": 1,
        "exp": 0,
        "hp": 60, 
        "max_hp": 60, 
        "atk": 6, 
        "spd": 6, 
        "rec": 12,
        "skill_name": "うずくまる", 
        "skill_type": "shield", 
        "skill_pow": 20, 
        "skill_trigger": "chance", 
        "skill_rate": 60,
        "best_equip": "", 
        "equip": None,
        "likes": {}, 
        "dislikes": {}, 
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": [],
    },
    {
        "name": "D2981", 
        "icon": "<:6_marin:1549696704788439101>", 
        "gender": "女", 
        "rarity": "★1", 
        "element": "光", 
        "role": "サポーター", 
        "atk_type": "魔法",
        "level": 1, 
        "exp": 0, 
        "hp": 50, 
        "max_hp": 50, 
        "atk": 2, 
        "spd": 5, 
        "rec": 20,
        "skill_name": "こうしたらいいの？", 
        "skill_type": "attract", 
        "skill_trigger": "chance", 
        "skill_rate": 75,
        "best_equip": "苦いクッキー", 
        "equip": None,
        "likes": {},
        "dislikes": {},
        "affection_level": 1, 
        "affection_exp": 0, 
        "known_likes": [], 
        "known_dislikes": [],
    },
    {
        "name": "レオ(仮面ライダーパロ)",
        "icon": "<:704_reo:1555165068927311882>",
        "gender": "男",
        "rarity": "★4",
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "level": 1,
        "exp": 0,
        "hp": 165,
        "max_hp": 165,
        "atk": 37,
        "spd": 24,
        "rec": 6,  
        "skill_name": "ドラゴニックフィニッシュ",
        "skill_type": "physical",
        "skill_pow": 65,
        "skill_trigger": "interval_3",
        "skill_rate": 95,
        "best_equip": "ビートクローザー",
        "equip": None,
        "likes": {"プロテインラーメン": "レオはこれを満足そうにガツガツと食べた。"},
        "dislikes": {},
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": [],
    },
    {
        "name": "ムクロ(トリッカルパロ)",
        "icon": "<:706_mukuro:1555165096819556453>",
        "gender": "？",
        "rarity": "★4",
        "element": "赤",
        "role": "アタッカー",
        "atk_type": "物理",
        "level": 1,
        "exp": 0,
        "hp": 100,
        "max_hp": 100,
        "atk": 24,
        "spd": 20,
        "rec": 4,
        "skill_name": "じゃーん、驚いたのだ？",
        "skill_type": "physical",
        "skill_pow": 40,
        "skill_trigger": "chance",
        "skill_rate": 78,
        "best_equip": "思い出の写真",
        "equip": None,
        "likes": {"ラムネ": "ムクロはラムネを飲まず、瓶だけ持ち帰ろうとした。"},
        "dislikes": {"アイスコーヒー": "ムクロはこれを一口飲んだが、露骨に嫌そうな顔をした。"},
        "affection_level": 1,
        "affection_exp": 0,
        "known_likes": [],
        "known_dislikes": [],
    },
]

# 🔻 「データ」フォルダにある追加キャラデータの読み込み
data_folder = "データ"
if os.path.exists(data_folder):
    for filename in os.listdir(data_folder):
        if filename.endswith(".py"):
            file_path = os.path.join(data_folder, filename)
            module_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "CHARACTER_DATA"):
                    data = getattr(module, "CHARACTER_DATA")
                    if isinstance(data, list):
                        GACHA_POOL.extend(data)
                    elif isinstance(data, dict):
                        GACHA_POOL.append(data)
                print(f"✨ 追加キャラデータの読み込み成功: {filename}")
            except Exception as e:
                print(f"⚠️ 追加キャラ読み込みエラー ({filename}): {e}")

def find_gacha_char(name):
    for c in GACHA_POOL:
        if c["name"] == name:
            return copy.deepcopy(c)
    return None

DEFAULT_CHARACTERS = [
    find_gacha_char("茉鈴"),
    find_gacha_char("橘柊人"),
    find_gacha_char("河野蜜柑")
]

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
    "にぼし": {"icon": ""},
    "虹色わたあめ": {"icon": ""},
    "アイスコーヒー": {"icon": ""},
}

def get_required_affection_exp(level):
    return level * 100

def check_affection_level_up(char_data, user_info):
    rewards = []
    MAX_AFFECTION_LEVEL = 30

    while True:
        if char_data["affection_level"] >= MAX_AFFECTION_LEVEL:
            char_data["affection_level"] = MAX_AFFECTION_LEVEL
            break

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
                rewards.append("🎁 ランダムご飯ボックス x1")
                user_info["items"]["ランダムご飯ボックス"] = user_info["items"].get("ランダムご飯ボックス", 0) + 1
        else:
            break

    return rewards

ALCOHOL_ITEMS = ["酒", "ビール", "ワイン", "ウイスキー", "日本酒"]
ADULT_CHARACTERS = [
    "折原和也", "橘柊人", "竹村しえら", "れーちゃん", "Gerânio", "レオ", "ロイ", 
    "白黒レイ", "神明龍矢", "サラ", "レオ(仮面ライダーパロ)", "彼方(ハロウィン)", "竜胆廉(ハロウィン)",
    "Branch Coral", "Root Coral",
]

def is_adult(char_name: str) -> bool:
    return char_name in ADULT_CHARACTERS

def is_child(char_name: str) -> bool:
    return not is_adult(char_name)
    
SUSPICIOUS_MEAT_ITEMS = ["怪しい肉"]
SUSPICIOUS_MEAT_CHARACTERS = [
    "Branch Coral", "Root Coral", "ロイ", "折原和也", "サラ",
]

def feed_character(user_info, char_data, food_name):
    char_name = char_data.get("name", "")

    if food_name in ALCOHOL_ITEMS and char_name not in ADULT_CHARACTERS:
        return {
            "status": "error",
            "reason": "underage_alcohol",
            "message": f"❌ **{char_name}** はお酒を飲むことができません！"
        }

    if food_name in SUSPICIOUS_MEAT_ITEMS and char_name not in SUSPICIOUS_MEAT_CHARACTERS:
        master_char = find_gacha_char(char_name) or {}
        if food_name not in master_char.get("dislikes", {}):
            return {
                "status": "error",
                "reason": "refused",
                "message": f"❌ **{char_name}** にこんなものあげようとしないでください！"
            }
        
    master_char = find_gacha_char(char_name) or {}
    master_likes = master_char.get("likes", {})
    master_dislikes = master_char.get("dislikes", {})

    if "known_likes" not in char_data: char_data["known_likes"] = []
    if "known_dislikes" not in char_data: char_data["known_dislikes"] = []
    if "known_special" not in char_data: char_data["known_special"] = []

    if food_name == "怪しい肉" and "怪しい肉" not in char_data["known_special"]:
        char_data["known_special"].append("怪しい肉")

    if "eaten_foods" not in char_data: char_data["eaten_foods"] = []

    is_first_time = food_name not in char_data["eaten_foods"]
    if is_first_time:
        char_data["eaten_foods"].append(food_name)
    
    is_like = food_name in master_likes
    is_dislike = food_name in master_dislikes

    if is_like:
        base_exp = 100
        taste_type = "like"
        if food_name not in char_data["known_likes"]: char_data["known_likes"].append(food_name)
    elif is_dislike:
        base_exp = 20
        taste_type = "dislike"
        if food_name not in char_data["known_dislikes"]: char_data["known_dislikes"].append(food_name)
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

def default_converter(o):
    if isinstance(o, set):
        return list(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

def _normalize_equipments(raw_eq):
    if isinstance(raw_eq, dict):
        return raw_eq
    eq_dict = {}
    if isinstance(raw_eq, list):
        for item in raw_eq:
            if isinstance(item, str):
                eq_dict[item] = eq_dict.get(item, 0) + 1
            elif isinstance(item, dict) and "name" in item:
                eq_name = item["name"]
                eq_dict[eq_name] = eq_dict.get(eq_name, 0) + 1
    return eq_dict

def load_data():
    global user_data
    if not sheet:
        print("⚠️ 【警告】sheetが初期化されていないため、読み込みをスキップしました。")
        return
    try:
        rows = sheet.get_all_values()
        user_data.clear()
        
        if len(rows) <= 1:
            print("📊 スプレッドシートにデータがありません。")
            return

        header = rows[0]
        is_old_format = "data_json" in header

        for row in rows[1:]:
            if not row or not row[0]:
                continue
            try:
                u_id = int(row[0])
            except ValueError:
                continue

            if is_old_format:
                try:
                    data_json_str = row[1] if len(row) > 1 and row[1] else "{}"
                    u_info = json.loads(data_json_str)
                    
                    user_data[u_id] = {
                        "gold": u_info.get("gold", 1000),
                        "u_level": u_info.get("u_level", 1),
                        "u_xp": u_info.get("u_xp", 0),
                        "win_count": u_info.get("win_count", 0),
                        "gamble_win_count": u_info.get("gamble_win_count", 0),
                        "unlocked_achievements": u_info.get("unlocked_achievements", []),
                        "characters": u_info.get("characters", []),
                        "items": u_info.get("items", {}),
                        "pieces": u_info.get("pieces", {}),  # 👈 かけら専用領域を追加
                        "equipments": _normalize_equipments(u_info.get("equipments", {})),
                        "party_indices": u_info.get("party_indices", [0, 1, 2]),
                        "mails": u_info.get("mails", [])
                    }
                except Exception as ex:
                    print(f"⚠️ ユーザーID {u_id} の旧データデコードエラー: {ex}")
            else:
                try:
                    raw_eq = json.loads(row[9]) if len(row) > 9 and row[9] else {}
                    user_data[u_id] = {
                        "gold": int(row[1]) if len(row) > 1 and row[1].isdigit() else 1000,
                        "u_level": int(row[2]) if len(row) > 2 and row[2].isdigit() else 1,
                        "u_xp": int(row[3]) if len(row) > 3 and row[3].isdigit() else 0,
                        "win_count": int(row[4]) if len(row) > 4 and row[4].isdigit() else 0,
                        "gamble_win_count": int(row[5]) if len(row) > 5 and row[5].isdigit() else 0,
                        "unlocked_achievements": json.loads(row[6]) if len(row) > 6 and row[6] else [],
                        "characters": json.loads(row[7]) if len(row) > 7 and row[7] else [],
                        "items": json.loads(row[8]) if len(row) > 8 and row[8] else {},
                        "pieces": json.loads(row[12]) if len(row) > 12 and row[12] else {},  # 👈 新形式: 12列目にpieces
                        "equipments": _normalize_equipments(raw_eq),
                        "party_indices": json.loads(row[10]) if len(row) > 10 and row[10] else [0, 1, 2],
                        "mails": json.loads(row[11]) if len(row) > 11 and row[11] else []
                    }
                except Exception as ex:
                    print(f"⚠️ ユーザーID {u_id} の新データ読み込みエラー: {ex}")

        print(f"📊 スプレッドシートから {len(user_data)} 人分のデータを完全に読み込みました！")
    except Exception as e:
        print(f"❌ データの読み込みエラー: {e}")

def _sync_save():
    if not sheet:
        return
    if not user_data:
        return

    try:
        rows = [[
            "user_id", "gold", "u_level", "u_xp", "win_count", "gamble_win_count",
            "unlocked_achievements", "characters", "items", "equipments", "party_indices", "mails", "pieces"
        ]]
        
        for u_id, data in user_data.items():
            rows.append([
                str(u_id),
                data.get("gold", 1000),
                data.get("u_level", 1),
                data.get("u_xp", 0),
                data.get("win_count", 0),
                data.get("gamble_win_count", 0),
                json.dumps(data.get("unlocked_achievements", []), ensure_ascii=False, default=default_converter),
                json.dumps(data.get("characters", []), ensure_ascii=False, default=default_converter),
                json.dumps(data.get("items", {}), ensure_ascii=False, default=default_converter),
                json.dumps(data.get("equipments", {}), ensure_ascii=False, default=default_converter),
                json.dumps(data.get("party_indices", [0, 1, 2]), ensure_ascii=False, default=default_converter),
                json.dumps(data.get("mails", []), ensure_ascii=False, default=default_converter),
                json.dumps(data.get("pieces", {}), ensure_ascii=False, default=default_converter)  # 👈 保存対象に追加
            ])
        
        sheet.clear()
        sheet.update(range_name='A1', values=rows)
        print("💾 スプレッドシートへ全データを列分割して保存しました。")
    except Exception as e:
        print(f"❌ データの保存エラー: {e}")

def save_data():
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _sync_save)
    except RuntimeError:
        _sync_save()

load_data()

def get_user_profile(user_id):
    user_id = int(user_id)
    if user_id not in user_data:
        user_data[user_id] = {
            "gold": 1000,
            "items": {"虹の欠片": 100, "ガチャチケ": 100, "装備ガチャチケット": 10, "おにぎり": 5, "ショートケーキ": 2, "激辛ラーメン": 2},
            "pieces": {},  # 👈 新規ユーザー用のかけら専用枠
            "characters": [copy.deepcopy(c) for c in DEFAULT_CHARACTERS if c],
            "equipments": {},
            "party_indices": [0, 1, 2],
            "mails": []
        }
        save_data()

    u_info = user_data[user_id]

    items = u_info.setdefault("items", {})
    if "装備ガチャチケット" not in items:
        items["装備ガチャチケット"] = 0
        
    u_info.setdefault("pieces", {})  # 👈 既存ユーザー向けにかけら枠を補完

    u_info["equipments"] = _normalize_equipments(u_info.get("equipments", {}))

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
            c["best_equip"] = master.get("best_equip", c.get("best_equip", None))

        if "element" not in c: c["element"] = master.get("element", "赤")
        if "role" not in c: c["role"] = master.get("role", "アタッカー")
        if "atk_type" not in c: c["atk_type"] = master.get("atk_type", "物理")
        if "gender" not in c: c["gender"] = master.get("gender", "？")
        if "best_equip" not in c: c["best_equip"] = master.get("best_equip", None)
        if "equip" not in c: c["equip"] = None
        if "likes" not in c: c["likes"] = master.get("likes", {})
        if "dislikes" not in c: c["dislikes"] = master.get("dislikes", {})
        if "affection_level" not in c: c["affection_level"] = 1
        if "affection_exp" not in c: c["affection_exp"] = 0
        if "known_likes" not in c: c["known_likes"] = []
        if "known_dislikes" not in c: c["known_dislikes"] = []
        if "known_special" not in c: c["known_special"] = []
        if "eaten_foods" not in c: c["eaten_foods"] = []

    return u_info

def add_equipment(user_info: dict, eq_name: str, count: int = 1):
    eq_dict = user_info.setdefault("equipments", {})
    eq_dict[eq_name] = eq_dict.get(eq_name, 0) + count

def get_available_equipment_count(user_info: dict, eq_name: str) -> int:
    owned_count = user_info.get("equipments", {}).get(eq_name, 0)
    equipped_count = sum(
        1 for c in user_info.get("characters", [])
        if c.get("equip") == eq_name
    )
    return max(0, owned_count - equipped_count)

save_data()
