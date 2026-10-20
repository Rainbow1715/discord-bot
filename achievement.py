import discord
from database import save_data, user_data
from discord.ext import commands

# --------------------------------------------------
# 🏆 実績の定義リスト
# --------------------------------------------------
ACHIEVEMENTS = {
    "first_win": {
        "title": "🔰 はじめての勝利",
        "desc": "バトルで1回勝利する",
        "reward_rainbow": 500,
    },
    "win_10": {
        "title": "⚔️ 百戦錬磨の兆し",
        "desc": "バトルで10回勝利する",
        "reward_rainbow": 1000,
    },
    "win_50": {
        "title": "⚔️ あと半分",
        "desc": "バトルで50回勝利する",
        "reward_rainbow": 5000,
    },
    "win_100": {
        "title": "⚔️ やるやん",
        "desc": "バトルで100回勝利する",
        "reward_rainbow": 10000,
    },
    "win_200": {
        "title": "⚔️ （ドン引き）",
        "desc": "バトルで200回勝利する",
        "reward_rainbow": 10000,
    },
    "win_300": {
        "title": "⚔️ 怖いって",
        "desc": "バトルで300回勝利する",
        "reward_rainbow": 10000,
    },
    "win_400": {
        "title": "⚔️ なにがおまえをそこまでかりたてるのか",
        "desc": "バトルで400回勝利する",
        "reward_rainbow": 10000,
    },
    "win_500": {
        "title": "⚔️ えぇ…",
        "desc": "バトルで500回勝利する",
        "reward_rainbow": 10000,
    },
    "win_1000": {
        "title": "⚔️ もはやバグだろ",
        "desc": "バトルで1000回勝利する",
        "reward_rainbow": 15000,
    },
    "win_1500": {
        "title": "⚔️ なんで解除できてるんですかこれ",
        "desc": "バトルで1500回勝利する",
        "reward_rainbow": 15000,
    },
    "gacha_1": {
        "title": "🔰 初めてのガチャ",
        "desc": "ガチャを累計1回引く",
        "reward_rainbow": 300,
    },
    "gacha_10": {
        "title": "🎰 ガチャ中毒",
        "desc": "ガチャを累計10回引く",
        "reward_rainbow": 800,
    },
    "gacha_50": {
        "title": "🎰 もうちょいで100",
        "desc": "ガチャを累計50回引く",
        "reward_rainbow": 1000,
    },
    "gacha_100": {
        "title": "🎰 真のガチャ中毒",
        "desc": "ガチャを累計100回引く",
        "reward_rainbow": 3000,
    },
    "gacha_200": {
        "title": "🎰 欲しいの出ました？",
        "desc": "ガチャを累計200回引く",
        "reward_rainbow": 5000,
    },
    "gacha_300": {
        "title": "🎰 すり抜けてる？",
        "desc": "ガチャを累計300回引く",
        "reward_rainbow": 5000,
    },
    "gacha_400": {
        "title": "🎰 そんなに回すことある？",
        "desc": "ガチャを累計400回引く",
        "reward_rainbow": 5000,
    },
    "gacha_500": {
        "title": "🎰 逆に何が欲しいか言ってごらん",
        "desc": "ガチャを累計500回引く",
        "reward_rainbow": 5000,
    },
    "gacha_600": {
        "title": "🎰 お望みのものが出ていないのですか？",
        "desc": "ガチャを累計600回引く",
        "reward_rainbow": 5000,
    },
    "gacha_700": {
        "title": "🎰 ラッキーセブンおめでと〜",
        "desc": "ガチャを累計777回引く",
        "reward_rainbow": 5000,
    },
    "gacha_800": {
        "title": "🎰 (バグじゃねぇのか？ と疑う顔)",
        "desc": "ガチャを累計800回引く",
        "reward_rainbow": 5000,
    },
    "gacha_900": {
        "title": "🎰 どんだけ引くんすか",
        "desc": "ガチャを累計900回引く",
        "reward_rainbow": 5000,
    },
    "gacha_1000": {
        "title": "🎰 こんだけ引けるってことは、報酬がイカれてるよな。わかってたけども。",
        "desc": "ガチャを累計1000回引く",
        "reward_rainbow": 10000,
    },
    # 🆕 特定キャラ編成で勝利の実績
    "win_siera_retya": {
        "title": "😰 ど、同一人物……",
        "desc": "竹村しえら と れーちゃん を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_siera_x3": {
        "title": "😰 ど、同一人物……②",
        "desc": "いずれかの 竹村しえら を3人編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_reo": {
        "title": "🤨 誰だお前？",
        "desc": "レオ と レオ(仮面ライダーパロ) を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_marin_orihara": {
        "title": "😰 なんでそんなことしたの？",
        "desc": "茉鈴 と 折原和也 を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_reo_roi": {
        "title": "🧐 なんでこんなことしたの？",
        "desc": "レオ と ロイ を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_roi_orihara_tatuya": {
        "title": "😟 カス三人衆を連れてきたよ①",
        "desc": "ロイ 折原和也 神明龍矢 を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_roi_sara_tatuya": {
        "title": "😟 カス三人衆を連れてきたよ②",
        "desc": "ロイ サラ 神明龍矢 を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_reo_sara": {
        "title": "🤩 弱虫毛虫、意気地なし！",
        "desc": "レオ サラ を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_tatuya_HWkanata": {
        "title": "😭 やめたげてよ",
        "desc": "神明龍矢 彼方(ハロウィン) を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    "win_Coral": {
        "title": "🖕 仲良し双子！",
        "desc": "Branch Coral  Root Coral を編成してバトルに勝利する",
        "reward_rainbow": 500,
    },
    # 👤 特定キャラ入手実績
    "get_kami": {
        "title": "❔ なんで？",
        "desc": "白黒レイ を獲得する",
        "reward_rainbow": 17000,
    },
    "get_rider_siera": {
        "title": "🚀 宇宙、キター！ ……はっず",
        "desc": "しえら(仮面ライダーパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_rider_reo": {
        "title": "🐉 今の俺は、負ける気がしねぇ！",
        "desc": "レオ(仮面ライダーパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_trickal_rucia": {
        "title": "🪅 一緒に遊ばない？",
        "desc": "ルシア(トリッカルパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_trickal_mukuro": {
        "title": "🙌 ぼくが遊びにきたのだよ。",
        "desc": "ムクロ(トリッカルパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_halloween_kanata": {
        "title": "🎃 と、トリックオア…トリート……？",
        "desc": "彼方(ハロウィン) を獲得する",
        "reward_rainbow": 200,
    },
    "get_rider_higurekou": {
        "title": "🦅 タ・ト・バ！ タトバ タ・ト・バ！",
        "desc": "日暮考(仮面ライダーパロ) を獲得する",
        "reward_rainbow": 200,
    },
    "get_halloween_rindouren": {
        "title": "🎃 お菓子ちょ〜だ〜い",
        "desc": "竜胆廉(ハロウィン) を獲得する",
        "reward_rainbow": 200,
    },
    # 💔 敗北系実績
    "first_lose": {
        "title": "🔰 最初の挫折",
        "desc": "初めてバトルで敗北する",
        "reward_rainbow": 200,
    },
    "lose_10": {
        "title": "🩹 七転び八起き",
        "desc": "累計10回バトルで敗北する",
        "reward_rainbow": 350,
    },
    "lose_50": {
        "title": "🩹 どしたん話聞こか？",
        "desc": "累計50回バトルで敗北する",
        "reward_rainbow": 500,
    },
    "lose_100": {
        "title": "🩹 うんうん、それは彼氏さんが悪いね！",
        "desc": "累計100回バトルで敗北する",
        "reward_rainbow": 500,
    },
    # 🎯 「初めて◯凸させた」系（最大到達凸数）
    "first_lb_1": {
        "title": "🔰 限界突破の第一歩",
        "desc": "初めてキャラクターを 1凸 (+1) させた",
        "reward_rainbow": 2000,
    },
    "first_lb_2": {
        "title": "🔰 ここまでは順調",
        "desc": "初めてキャラクターを 2凸 (+2) させた",
        "reward_rainbow": 5000,
    },
    "first_lb_3": {
        "title": "🔰 さらなる高みへ",
        "desc": "初めてキャラクターを 3凸 (+3) させた",
        "reward_rainbow": 10000,
    },
    "first_lb_4": {
        "title": "🔰 まだ行けるか？",
        "desc": "初めてキャラクターを 4凸 (+4) させた",
        "reward_rainbow": 30000,
    },
    "first_lb_5": {
        "title": "🔰 極限突破",
        "desc": "初めてキャラクターを 5凸 (+5、完凸) させた",
        "reward_rainbow": 50000,
    },
    # 🔄 「累計◯回凸させた」系（合計実行回数）
    "total_lb_1": {
        "title": "🔰 初心者クラフター",
        "desc": "累計で 1回 限界突破を行った",  # 👈 "description" から "desc" に修正！
        "reward_rainbow": 1000,
    },
    "total_lb_5": {
        "title": "🆙 ベテランクラフター",
        "desc": "累計で 5回 限界突破を行った",  # 👈 "description" から "desc" に修正！
        "reward_rainbow": 15000,
    },
    "total_lb_10": {
        "title": "🆙 限界突破マニア",
        "desc": "累計で 10回 限界突破を行った", # 👈 "description" から "desc" に修正！
        "reward_rainbow": 50000,
    },
    # 👹 イベントボス撃破実績
    "kill_roi": {
        "title": "⚔️ カス討伐：ロイ",
        "desc": "イベント戦で ロイ を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_orihara": {
        "title": "⚔️ カス討伐：折原和也",
        "desc": "イベント戦で 折原和也 を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_tatsuya": {
        "title": "⚔️ カス討伐：神明龍矢",
        "desc": "イベント戦で 神明龍矢 を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_sara": {
        "title": "⚔️ カス討伐：サラ",
        "desc": "イベント戦で サラ を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_rider_aria": {
        "title": "⚔️ ドラゴンフルボトルゲット",
        "desc": "イベント戦で アリア を撃破する",
        "reward_rainbow": 1000,
    },
    "kill_rider_ptkou": {
        "title": "⚔️ 消滅した紫のコアメダル",
        "desc": "イベント戦で 日暮考(プトティラコンボ) を撃破する",
        "reward_rainbow": 1000,
    },
    # 🎰 ギャンブル実績
    "win_gamble_1": {
        "title": "🔰 ギャンカスの一歩",
        "desc": "ギャンブルで一回勝利する",
        "reward_rainbow": 500,
    },
    "win_gamble_10": {
        "title": "🃏 まさか一発でこんだけ勝ったわけあるまいな",
        "desc": "ギャンブルで10回勝利する",
        "reward_rainbow": 500,
    },
    "win_gamble_50": {
        "title": "🃏 おお",
        "desc": "ギャンブルで50回勝利する",
        "reward_rainbow": 500,
    },
    "win_gamble_100": {
        "title": "🃏 おおじゃないが",
        "desc": "ギャンブルで100回勝利する",
        "reward_rainbow": 500,
    },
    "win_gamble_500": {
        "title": "🃏 これはおおだろ",
        "desc": "ギャンブルで500回勝利する",
        "reward_rainbow": 500,
    },
    # ----------------
    # --- 竹村しえら ---
    "gamble_竹村しえら_8": {
        "title": "🃏 しえらの深淵⑧", 
        "desc": "竹村しえらのギャンブル敗北セリフ8回目を見る", 
        "reward_rainbow": 500},
    "gamble_竹村しえら_9": {
        "title": "🃏 しえらの深淵⑨", 
        "desc": "竹村しえらのギャンブル敗北セリフ9回目を見る", 
        "reward_rainbow": 1000},
    "gamble_竹村しえら_10": {
        "title": "🃏 しえらの深淵⑩", 
        "desc": "竹村しえらのギャンブル敗北セリフ10回目を見る", 
        "reward_rainbow": 2000},
    "win_gamble_siera": {
        "title": "🃏 しえらに勝利",
        "desc": "ギャンブルで しえら に勝利する",
        "reward_rainbow": 500,
    },
    # --- サラ ---
    "gamble_サラ_8": {
        "title": "🃏 サラの深淵⑧", 
        "desc": "サラのギャンブル敗北セリフ8回目を見る", 
        "reward_rainbow": 500},
    "gamble_サラ_9": {
        "title": "🃏 サラの深淵⑨", 
        "desc": "サラのギャンブル敗北セリフ9回目を見る", 
        "reward_rainbow": 1000},
    "gamble_サラ_10": {
        "title": "🃏 サラの深淵⑩", 
        "desc": "サラのギャンブル敗北セリフ10回目を見る", 
        "reward_rainbow": 2000},
    "win_gamble_sara": {
        "title": "🃏 サラに勝利",
        "desc": "ギャンブルで サラ に勝利する",
        "reward_rainbow": 500,
    },
    # --- 折原(にょた) ---
    "gamble_折原(にょた)_8": {
        "title": "🃏 にょた原の深淵⑧", 
        "desc": "折原(にょた)のギャンブル敗北セリフ8回目を見る", 
        "reward_rainbow": 500},
    "gamble_折原(にょた)_9": {
        "title": "🃏 にょた原の深淵⑨", 
        "desc": "折原(にょた)のギャンブル敗北セリフ9回目を見る", 
        "reward_rainbow": 1000},
    "gamble_折原(にょた)_10": {
        "title": "🃏 にょた原の深淵⑩", 
        "desc": "折原(にょた)のギャンブル敗北セリフ10回目を見る", 
        "reward_rainbow": 2000},
    "win_gamble_nyotahara": {
        "title": "🃏 にょた原さんに勝利",
        "desc": "ギャンブルで 折原(にょた) に勝利する",
        "reward_rainbow": 500,
    },
    # --- ロイ ---
    "gamble_ロイ_8": {
        "title": "🃏 ロイの深淵⑧", 
        "desc": "ロイのギャンブル敗北セリフ8回目を見る", 
        "reward_rainbow": 500},
    "gamble_ロイ_9": {
        "title": "🃏 ロイの深淵⑨", 
        "desc": "ロイのギャンブル敗北セリフ9回目を見る", 
        "reward_rainbow": 1000},
    "gamble_ロイ_10": {
        "title": "🃏 ロイの深淵⑩", 
        "desc": "ロイのギャンブル敗北セリフ10回目を見る", 
        "reward_rainbow": 2000},
    "win_gamble_roi": {
        "title": "🃏 ロイに勝利",
        "desc": "ギャンブルで ロイ に勝利する",
        "reward_rainbow": 500,
    },
    # --- 彼方 ---
    "gamble_彼方_8": {
        "title": "🃏 彼方の深淵⑧", 
        "desc": "彼方のギャンブル敗北セリフ8回目を見る", 
        "reward_rainbow": 500},
    "gamble_彼方_9": {
        "title": "🃏 彼方の深淵⑨", 
        "desc": "彼方のギャンブル敗北セリフ9回目を見る", 
        "reward_rainbow": 1000},
    "gamble_彼方_10": {
        "title": "🃏 彼方の深淵⑩", 
        "desc": "彼方のギャンブル敗北セリフ10回目を見る", 
        "reward_rainbow": 2000},
    "win_gamble_kanata": {
        "title": "🃏 彼方に勝利",
        "desc": "ギャンブルで 彼方 に勝利する",
        "reward_rainbow": 500,
    },
    # -----------------------
    # キャラごと実績
    # --------------------------
    "eat_siera": {
        "title": "🍽️ しえらの嫌いなもの",
        "desc": "竹村しえら に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_siera": {
        "title": "🍽️ しえらの好きなもの",
        "desc": "竹村しえら に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_siera": {
        "title": "✨ これだよこれ！（しえら）",
        "desc": "竹村しえら に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_retyan": {
        "title": "🍽️ れーちゃんの嫌いなもの",
        "desc": "れーちゃん に嫌いなものを食べさせた",
        "reward_rainbow": 150,
    },
    "eatlike_retyan": {
        "title": "🍽️ れーちゃんの好きなもの",
        "desc": "れーちゃん に好きなものを食べさせた",
        "reward_rainbow": 150,
    },
    "equip_best_retya": {
        "title": "✨ これだよこれ！（れーちゃん）",
        "desc": "れーちゃん に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_reo": {
        "title": "🍽️ レオの嫌いなもの",
        "desc": "レオ に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_reo": {
        "title": "🍽️ レオの好きなもの",
        "desc": "レオ に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_reo": {
        "title": "✨ これだよこれ！（レオ）",
        "desc": "レオ に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_touwata": {
        "title": "🍽️ 唐綿さんの嫌いなもの",
        "desc": "Gerânio に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_touwata": {
        "title": "🍽️ 唐綿さんの好きなもの",
        "desc": "Gerânio に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_touwata": {
        "title": "✨ これだよこれ！（唐綿さん）",
        "desc": "Gerânio に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_skrei": {
        "title": "🍽️ xX神Xxの嫌いなもの",
        "desc": "白黒レイ に嫌いなものを食べさせた",
        "reward_rainbow": 500,
    },
    "eatlike_skrei": {
        "title": "🍽️ xX神Xxの好きなもの",
        "desc": "白黒レイ に好きなものを食べさせた",
        "reward_rainbow": 500,
    },
    "equip_best_skrei": {
        "title": "✨ これだよこれ！（xX_神_Xx）",
        "desc": "白黒レイ に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_marin": {
        "title": "🍽️ 茉鈴の嫌いなもの",
        "desc": "茉鈴 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_marin": {
        "title": "🍽️ 茉鈴の好きなもの",
        "desc": "茉鈴 に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_marin": {
        "title": "✨ これだよこれ！（茉鈴）",
        "desc": "茉鈴 に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_syuuto": {
        "title": "🍽️ 柊人の嫌いなもの",
        "desc": "橘柊人 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_syuuto": {
        "title": "🍽️ 柊人の好きなもの",
        "desc": "橘柊人 に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_syuuto": {
        "title": "✨ これだよこれ！（柊人）",
        "desc": "橘柊人 に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_mikan": {
        "title": "🍽️ 河野蜜柑の嫌いなもの",
        "desc": "河野蜜柑 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_mikan": {
        "title": "🍽️ 河野蜜柑の好きなもの",
        "desc": "河野蜜柑 に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_mikan": {
        "title": "✨ これだよこれ！（蜜柑）",
        "desc": "河野蜜柑 に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_roi": {
        "title": "🍽️ ロイの嫌いなもの",
        "desc": "ロイ に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_roi": {
        "title": "🍽️ ロイの好きなもの",
        "desc": "ロイ に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_roi": {
        "title": "✨ これだよこれ！（ロイ）",
        "desc": "ロイ に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_orihara": {
        "title": "🍽️ 折原さんの嫌いなもの",
        "desc": "折原和也 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_orihara": {
        "title": "🍽️ 折原さんの好きなもの",
        "desc": "折原和也 に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_orihara": {
        "title": "✨ これだよこれ！（折原さん）",
        "desc": "折原和也 に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_tatuya": {
        "title": "🍽️ 神明龍矢の嫌いなもの",
        "desc": "神明龍矢 に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_tatuya": {
        "title": "🍽️ 神明龍矢の好きなもの",
        "desc": "神明龍矢 に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_tatuya": {
        "title": "✨ これだよこれ！（神明龍矢）",
        "desc": "神明龍矢 に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_sara": {
        "title": "🍽️ サラの嫌いなもの",
        "desc": "サラ に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_sara": {
        "title": "🍽️ サラの好きなもの",
        "desc": "サラ に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_sara": {
        "title": "✨ これだよこれ！（サラ）",
        "desc": "サラ に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_rider_reo": {
        "title": "🍽️ レオ(仮面ライダーパロ)の嫌いなもの",
        "desc": "レオ(仮面ライダーパロ) に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_rider_reo": {
        "title": "🍽️ レオ(仮面ライダーパロ)の好きなもの",
        "desc": "レオ(仮面ライダーパロ) に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_riderreo": {
        "title": "✨ これだよこれ！（レオ(仮面ライダーパロ)）",
        "desc": "レオ(仮面ライダーパロ) に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_trickcal_mukuro": {
        "title": "🍽️ ムクロ(トリッカルパロ)の嫌いなもの",
        "desc": "ムクロ(トリッカルパロ) に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_trickcal_mukuro": {
        "title": "🍽️ ムクロ(トリッカルパロ)の好きなもの",
        "desc": "ムクロ(トリッカルパロ) に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_trickcalmukuro": {
        "title": "✨ これだよこれ！（ムクロ(トリッカルパロ)）",
        "desc": "ムクロ(トリッカルパロ) に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_rider_siera": {
        "title": "🍽️ しえら(仮面ライダーパロ)の嫌いなもの",
        "desc": "しえら(仮面ライダーパロ) に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_rider_siera": {
        "title": "🍽️ しえら(仮面ライダーパロ)の好きなもの",
        "desc": "しえら(仮面ライダーパロ) に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_ridersiera": {
        "title": "✨ これだよこれ！（しえら(仮面ライダーパロ)）",
        "desc": "しえら(仮面ライダーパロ) に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    "eat_trickcal_rucia": {
        "title": "🍽️ ルシア(トリッカルパロ)の嫌いなもの",
        "desc": "ルシア(トリッカルパロ) に嫌いなものを食べさせた",
        "reward_rainbow": 100,
    },
    "eatlike_trickcal_rucia": {
        "title": "🍽️ ルシア(トリッカルパロ)の好きなもの",
        "desc": "ルシア(トリッカルパロ) に好きなものを食べさせた",
        "reward_rainbow": 100,
    },
    "equip_best_rucia": {
        "title": "✨ これだよこれ！（ルシア(トリッカルパロ)）",
        "desc": "ルシア(トリッカルパロ) に適正装備を装着させる",
        "reward_rainbow": 500,
    },
    
    # 怪しい肉
    "meat_akakun": {
        "title": "🍖 赤くんになんか食べさせた",
        "desc": "Branch Coral に怪しい肉を食べさせた",
        "reward_rainbow": 100,
    },
    "meat_sangokun": {
        "title": "🍖 珊瑚くんになんか食べさせた",
        "desc": "Root Coral に怪しい肉を食べさせた",
        "reward_rainbow": 100,
    },
    "meat_roi": {
        "title": "🍖 ロイになんか食べさせようとした",
        "desc": "ロイ に怪しい肉をあげた",
        "reward_rainbow": 100,
    },
    "meat_orihara": {
        "title": "🍖 折原さんになんか食べさせようとした",
        "desc": "折原和也 に怪しい肉をあげた",
        "reward_rainbow": 100,
    },
    "meat_sara": {
        "title": "🍖 サラになんか食べさせようとした",
        "desc": "サラ に怪しい肉をあげた",
        "reward_rainbow": 100,
    },
    # 🗡️ キャラ別の適正装備実績
    "equip_best_d2981": {
        "title": "✨ なんでこいつ適正装備あんの？",
        "desc": "D2981 に適正装備を装着させる",
        "reward_rainbow": 500,
    },

}

LOG_CHANNEL_ID = 1547122457062940712


# --------------------------------------------------
# 🔓 実績解除・通知共通関数
# --------------------------------------------------
async def check_and_unlock_achievement(
    interaction: discord.Interaction, achievement_id: str
):
    u_id = interaction.user.id
    u_data = user_data.get(u_id)
    if not u_data:
        return

    if "unlocked_achievements" not in u_data:
        u_data["unlocked_achievements"] = []

    if achievement_id in u_data["unlocked_achievements"]:
        return

    ach = ACHIEVEMENTS.get(achievement_id)
    if not ach:
        return

    u_data["unlocked_achievements"].append(achievement_id)
    reward_rainbow = ach.get("reward_rainbow", 0)

    if "items" not in u_data:
        u_data["items"] = {}
    u_data["items"]["虹の欠片"] = (
        u_data["items"].get("虹の欠片", 0) + reward_rainbow
    )

    save_data()

    # 🔔 通知①：本人へのメッセージ
    reward_str = (
        f"💎 虹の欠片 {reward_rainbow}個" if reward_rainbow > 0 else "なし"
    )
    embed_user = discord.Embed(
        title="🎉 実績を解除しました！",
        description=f"**{ach['title']}**\n└ {ach['desc']}\n\n🎁 **獲得報酬**: {reward_str}",
        color=0xF1C40F,
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed_user, ephemeral=True)
        else:
            await interaction.response.send_message(
                embed=embed_user, ephemeral=True
            )
    except Exception as e:
        print(f"本人への実績通知エラー: {e}")

    # 📢 通知②：ログチャンネルへの投稿
    try:
        target_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if target_channel:
            await target_channel.send(
                f"{interaction.user.mention} が 実績【{ach['title']}】を解除しました！"
            )
        else:
            print(
                f"⚠️ 指定されたチャンネルID ({LOG_CHANNEL_ID}) が見つかりませんでした。"
            )
    except Exception as e:
        print(f"ログチャンネルへの実績通知エラー: {e}")


# --------------------------------------------------
# 🗡️ キャラ名と適正装備実績IDのマッピング辞書
# --------------------------------------------------
BEST_EQUIP_CHAR_MAP = {
    "竹村しえら": "equip_best_siera",
    "れーちゃん": "equip_best_retya",
    "レオ": "equip_best_reo",
    "Gerânio": "equip_best_touwata",
    "白黒レイ": "equip_best_skrei",
    "茉鈴": "equip_best_marin",
    "橘柊人": "equip_best_syuuto",
    "河野蜜柑": "equip_best_mikan",
    "ロイ": "equip_best_roi",
    "折原和也": "equip_best_orihara",
    "神明龍矢": "equip_best_tatuya",
    "サラ": "equip_best_sara",
    "D2981": "equip_best_d2981",
    "レオ(仮面ライダーパロ)": "equip_best_riderreo",
    "ムクロ(トリッカルパロ)": "equip_best_trickcalmukuro",
    "しえら(仮面ライダーパロ)": "equip_best_ridersiera",
    "ルシア(トリッカルパロ)": "equip_best_rucia",
    "彼方(ハロウィン)": "equip_best_HWkanata",
    "竜胆廉(ハロウィン)": "equip_best_HWrindouren",
    "Branch Coral": "equip_best_akakun",
    "Root Coral": "equip_best_sangokun",
}


async def check_equip_best_achievement(
    interaction: discord.Interaction, char_data: dict, equip_name: str
):
    """キャラごとに適正装備判定をして実績解除（複数対応版）"""
    char_name = char_data.get("name")
    best_equip = char_data.get("best_equip")  # 👈 ここがリストになる想定

    is_match = False
    if isinstance(best_equip, list):
        # リストの場合は、装備しようとしている名前がリストのどれかに含まれるか
        is_match = equip_name in best_equip
    elif isinstance(best_equip, dict):
        # 従来の辞書型や互換性のための保険
        best_name = best_equip.get("name")
        is_match = (equip_name == best_name)
    else:
        # 従来の文字列の保険
        is_match = (equip_name == best_equip)

    if is_match:
        ach_id = BEST_EQUIP_CHAR_MAP.get(char_name)
        if ach_id:
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# ⚔️ バトル勝利時の自動実績チェック
# --------------------------------------------------
WIN_THRESHOLD_ACHIEVEMENTS = [
    (1, "first_win"),
    (10, "win_10"),
    (50, "win_50"),
    (100, "win_100"),
    (200, "win_200"),
    (300, "win_300"),
    (400, "win_400"),
    (500, "win_500"),
    (1000, "win_1000"),
    (1500, "win_1500"),
]


async def on_battle_win(interaction: discord.Interaction, u_data: dict):
    u_data["win_count"] = u_data.get("win_count", 0) + 1
    win_count = u_data["win_count"]

    for threshold, ach_id in WIN_THRESHOLD_ACHIEVEMENTS:
        if win_count >= threshold:
            await check_and_unlock_achievement(interaction, ach_id)

    party_indices = u_data.get("party_indices", [])
    characters = u_data.get("characters", [])

    party_names = []
    for idx in party_indices:
        if isinstance(idx, int) and idx < len(characters):
            char_data = characters[idx]
            if isinstance(char_data, dict) and "name" in char_data:
                party_names.append(char_data["name"])

    party_names_set = set(party_names)

    if {"竹村しえら", "れーちゃん"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_siera_retya")

    siera_count = sum(1 for name in party_names if "しえら" in name)
    if siera_count >= 3:
        await check_and_unlock_achievement(interaction, "win_siera_x3")

    if {"レオ", "レオ(仮面ライダーパロ)"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_reo")

    if {"茉鈴", "折原和也"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_marin_orihara")

    if {"レオ", "ロイ"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_reo_roi")

    if {"ロイ", "折原和也", "神明龍矢"}.issubset(party_names_set):
        await check_and_unlock_achievement(
            interaction, "win_roi_orihara_tatuya")

    if {"ロイ", "サラ", "神明龍矢"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_roi_sara_tatuya")

    if {"レオ", "サラ"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_reo_sara")

    if {"神明龍矢", "彼方(ハロウィン)"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_tatuya_HWkanata")

    if {"Branch Coral", "Root Coral"}.issubset(party_names_set):
        await check_and_unlock_achievement(interaction, "win_Coral")



# --------------------------------------------------
# 💔 バトル敗北時の自動実績チェック
# --------------------------------------------------
async def on_battle_lose(interaction: discord.Interaction, u_data: dict):
    u_data["lose_count"] = u_data.get("lose_count", 0) + 1
    lose_count = u_data["lose_count"]

    await check_and_unlock_achievement(interaction, "first_lose")
    if lose_count >= 10:
        await check_and_unlock_achievement(interaction, "lose_10")
    if lose_count >= 50:
        await check_and_unlock_achievement(interaction, "lose_50")
    if lose_count >= 100:
        await check_and_unlock_achievement(interaction, "lose_100")


# --------------------------------------------------
# 🌟 限界突破時の自動実績チェック
# --------------------------------------------------
async def check_limit_break_achievements(
    interaction: discord.Interaction, u_data: dict, new_lb: int
):
    """
    限界突破時に呼び出される関数。
    new_lb: 今回達した凸数（例: 1〜5）
    """
    # 1. 累計回数のインクリメント
    total_lb_count = u_data.get("total_lb_count", 0) + 1
    u_data["total_lb_count"] = total_lb_count

    # 2. 最高到達凸数の記録
    max_lb = max(u_data.get("max_lb_reached", 0), new_lb)
    u_data["max_lb_reached"] = max_lb

    # --------------------------------------------------
    # 判定1: 「初めて◯凸」系 (1, 2, 3, 4, 5)
    # --------------------------------------------------
    first_targets = [
        (1, "first_lb_1"),
        (2, "first_lb_2"),
        (3, "first_lb_3"),
        (4, "first_lb_4"),
        (5, "first_lb_5"),
    ]
    for target_lb, ach_id in first_targets:
        if max_lb >= target_lb:
            await check_and_unlock_achievement(interaction, ach_id)

    # --------------------------------------------------
    # 判定2: 「累計◯回」系
    # --------------------------------------------------
    total_targets = [
        (1, "total_lb_1"),
        (5, "total_lb_5"),
        (10, "total_lb_10"),
    ]
    for target_count, ach_id in total_targets:
        if total_lb_count >= target_count:
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# 👹 イベントボス撃破時の自動実績チェック
# --------------------------------------------------
async def check_boss_kill_achievements(
    interaction: discord.Interaction, defeated_enemy_names: list
):
    boss_mapping = {
        "ロイ": "kill_roi",
        "折原和也": "kill_orihara",
        "神明龍矢": "kill_tatsuya",
        "サラ": "kill_sara",
        "アリア(仮面ライダーパロ)": "kill_rider_aria",
        "日暮考(プトティラコンボ)": "kill_rider_ptkou",
    }

    for boss_name, ach_id in boss_mapping.items():
        if any(boss_name in enemy_name for enemy_name in defeated_enemy_names):
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# 🎰 ガチャ実行時の自動実績チェック
# --------------------------------------------------
async def on_gacha_draw(
    interaction: discord.Interaction, u_data: dict, draw_count: int = 0
):
    if draw_count > 0:
        u_data["gacha_count"] = u_data.get("gacha_count", 0) + draw_count

    count = u_data.get("gacha_count", 0)

    if count >= 1:
        await check_and_unlock_achievement(interaction, "gacha_1")
    if count >= 10:
        await check_and_unlock_achievement(interaction, "gacha_10")
    if count >= 50:
        await check_and_unlock_achievement(interaction, "gacha_50")
    if count >= 100:
        await check_and_unlock_achievement(interaction, "gacha_100")
    if count >= 200:
        await check_and_unlock_achievement(interaction, "gacha_200")
    if count >= 300:
        await check_and_unlock_achievement(interaction, "gacha_300")
    if count >= 400:
        await check_and_unlock_achievement(interaction, "gacha_400")
    if count >= 500:
        await check_and_unlock_achievement(interaction, "gacha_500")
    if count >= 600:
        await check_and_unlock_achievement(interaction, "gacha_600")
    if count >= 777:  # 👈 gacha_700 の条件（777回）に合わせる
        await check_and_unlock_achievement(interaction, "gacha_700")
    if count >= 800:
        await check_and_unlock_achievement(interaction, "gacha_800")
    if count >= 900:
        await check_and_unlock_achievement(interaction, "gacha_900")
    if count >= 1000:
        await check_and_unlock_achievement(interaction, "gacha_1000")



# --------------------------------------------------
# 🎴 特定キャラ獲得時の自動実績チェック
# --------------------------------------------------
async def check_character_achievements(
    interaction: discord.Interaction,
    u_data: dict,
    obtained_character_names: list,
):
    mapping = {
        "白黒レイ": "get_kami",
        "しえら(仮面ライダーパロ)": "get_rider_siera",
        "レオ(仮面ライダーパロ)": "get_rider_reo",
        "ルシア(トリッカルパロ)": "get_trickal_rucia",
        "ムクロ(トリッカルパロ)": "get_trickal_mukuro",
        "彼方(ハロウィン)": "get_halloween_kanata",
        "日暮考(仮面ライダーパロ)": "get_rider_higurekou",
        "竜胆廉(ハロウィン)": "get_halloween_rindouren",
    }

    for name, ach_id in mapping.items():
        if name in obtained_character_names:
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# 🍽️ 食事実行時の自動実績チェック
# --------------------------------------------------
async def check_eat_dislike_achievement(
    interaction: discord.Interaction,
    char_id: str,
    food_name: str,
    char_data: dict,
):
    dislikes = char_data.get("dislikes", [])
    is_disliked = any(dislike_item in food_name for dislike_item in dislikes)

    if is_disliked:
        ach_id = f"eat_{char_id}"
        await check_and_unlock_achievement(interaction, ach_id)


async def check_eat_like_achievement(
    interaction: discord.Interaction,
    char_id: str,
    food_name: str,
    char_data: dict,
):
    likes = char_data.get("likes", [])
    is_liked = any(like_item in food_name for like_item in likes)

    if is_liked:
        ach_id = f"eatlike_{char_id}"
        await check_and_unlock_achievement(interaction, ach_id)


async def check_eat_suspicious_meat_achievement(
    interaction: discord.Interaction,
    char_id: str,
    food_name: str,
):
    if "怪しい肉" in food_name:
        meat_mapping = {
            "Branch Coral": "meat_akakun",
            "Root Coral": "meat_sangokun",
            "ロイ": "meat_roi",
            "折原和也": "meat_orihara",
            "サラ": "meat_sara",
        }
        ach_id = meat_mapping.get(char_id)
        if ach_id:
            await check_and_unlock_achievement(interaction, ach_id)


# --------------------------------------------------
# 🎰 ギャンブル勝利時の自動実績チェック
# --------------------------------------------------
async def on_gamble_win(
    interaction: discord.Interaction, u_data: dict, opponent_name: str = None
):
    u_data["gamble_win_count"] = u_data.get("gamble_win_count", 0) + 1
    gamble_wins = u_data["gamble_win_count"]

    if gamble_wins >= 1:
        await check_and_unlock_achievement(interaction, "win_gamble_1")
    if gamble_wins >= 10:
        await check_and_unlock_achievement(interaction, "win_gamble_10")
    if gamble_wins >= 50:
        await check_and_unlock_achievement(interaction, "win_gamble_50")
    if gamble_wins >= 100:
        await check_and_unlock_achievement(interaction, "win_gamble_100")
    if gamble_wins >= 500:
        await check_and_unlock_achievement(interaction, "win_gamble_500")


async def on_gamble_match_win(
    interaction: discord.Interaction, u_data: dict, opponent_name: str
):
    if opponent_name:
        opponent_mapping = {
            "しえら": "win_gamble_siera",
            "サラ": "win_gamble_sara",
            "折原(にょた)": "win_gamble_nyotahara",
            "ロイ": "win_gamble_roi",
            "彼方": "win_gamble_kanata",
        }
        for name_key, ach_id in opponent_mapping.items():
            if name_key in opponent_name:
                await check_and_unlock_achievement(interaction, ach_id)

async def check_character_gamble_line_achievement(
    interaction: discord.Interaction, char_name: str, line_num: int
):
    """キャラ名と回数（8, 9, 10）を組み合わせて実績IDを自動生成し、解除判定を行う"""
    if line_num in [8, 9, 10]:
        ach_id = f"gamble_{char_name}_{line_num}"
        await check_and_unlock_achievement(interaction, ach_id)

# --------------------------------------------------
# 🤖 実績確認コマンド (/achievements)
# --------------------------------------------------
class AchievementCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="achievements", description="実績の獲得状況を確認します"
    )
    async def achievements(self, interaction: discord.Interaction):
        u_data = user_data.get(interaction.user.id, {})
        unlocked = u_data.get("unlocked_achievements", [])

        embeds = []
        current_embed = discord.Embed(
            title=f"🏆 {interaction.user.display_name} の実績一覧",
            color=0xF1C40F,
        )
        field_count = 0

        for ach_id, ach in ACHIEVEMENTS.items():
            if field_count >= 20:
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title=f"🏆 {interaction.user.display_name} の実績一覧 (続き)",
                    color=0xF1C40F,
                )
                field_count = 0

            status = "✅ 達成済み" if ach_id in unlocked else "🔒 未達成"
            reward_val = ach.get("reward_rainbow", 0)
            reward_info = (
                f" (🎁 虹の欠片 {reward_val}個)" if reward_val > 0 else ""
            )

            current_embed.add_field(
                name=f"{ach['title']} ({status})",
                value=f"{ach['desc']}{reward_info}",
                inline=False,
            )
            field_count += 1

        embeds.append(current_embed)

        await interaction.response.send_message(
            embed=embeds[0], ephemeral=True
        )
        for extra_embed in embeds[1:]:
            await interaction.followup.send(embed=extra_embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
