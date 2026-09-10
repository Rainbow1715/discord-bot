from database import user_data, GACHA_POOL, save_data

def recalculate_all_characters():
    print("🔄 全ユーザーのキャラクターデータ再計算を開始します...")
    
    updated_users = 0
    updated_chars = 0

    for user_id, u_data in user_data.items():
        characters = u_data.get("characters", [])
        for char in characters:
            # GACHA_POOL から基礎データを取得
            template = next((c for c in GACHA_POOL if c["name"] == char["name"]), None)
            if not template:
                continue

            # 1. レベルによる上昇分（例: Lv.1ごとに HP+10, ATK+2 と仮定）
            # ※現在のプロジェクトのレベル上昇処理に合わせて調整してください
            level = char.get("level", 1)
            level_hp_bonus = (level - 1) * 10
            level_atk_bonus = (level - 1) * 2

            # 2. ランクアップ（★）による上昇分（初期値の 20% × ランクアップ回数）
            # ★3が初期値の場合：★4なら1回分、★5なら2回分
            base_rarity = template.get("rarity", "★3")
            current_rarity = char.get("rarity", base_rarity)
            
            # ★の数を数値化
            rarity_map = {"★1": 1, "★2": 2, "★3": 3, "★4": 4, "★5": 5}
            rank_diff = max(0, rarity_map.get(current_rarity, 3) - rarity_map.get(base_rarity, 3))

            base_hp = template.get("hp", 100)
            base_atk = template.get("atk", 10)

            rank_hp_bonus = int(base_hp * 0.20) * rank_diff
            rank_atk_bonus = int(base_atk * 0.20) * rank_diff

            # 3. 本来あるべき正しいステータスを再計算して上書き
            correct_hp = base_hp + level_hp_bonus + rank_hp_bonus
            correct_atk = base_atk + level_atk_bonus + rank_atk_bonus

            char["hp"] = correct_hp
            if "max_hp" in char:
                char["max_hp"] = correct_hp
            char["atk"] = correct_atk

            updated_chars += 1
        updated_users += 1

    save_data()
    print(f"✅ 再計算が完了しました！（対象: {updated_users} ユーザー / {updated_chars} キャラクター）")

if __name__ == "__main__":
    recalculate_all_characters()
