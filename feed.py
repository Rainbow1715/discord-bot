def feed_character(user_data, char_data, food_name):
    char_name = char_data["name"]
    taste = CHARACTER_TASTE.get(char_name, {"likes": [], "dislikes": []})
    
    # 既存の記録用リストがなければ初期化
    if "known_likes" not in char_data:
        char_data["known_likes"] = []
    if "known_dislikes" not in char_data:
        char_data["known_dislikes"] = []

    # 初めて食べるご飯かどうかのチェック
    is_first_time = (food_name not in char_data["known_likes"]) and (food_name not in char_data["known_dislikes"])
    
    # 基本XPの判定
    if food_name in taste["likes"]:
        base_exp = 100
        taste_type = "like"
        if food_name not in char_data["known_likes"]:
            char_data["known_likes"].append(food_name)
    elif food_name in taste["dislikes"]:
        base_exp = 20
        taste_type = "dislike"
        if food_name not in char_data["known_dislikes"]:
            char_data["known_dislikes"].append(food_name)
    else:
        base_exp = 50
        taste_type = "normal"

    # 初回ボーナス +20xp
    first_bonus = 20 if is_first_time else 0
    total_gained_exp = base_exp + first_bonus

    # 経験値・なつき度の加算
    char_data["exp"] = char_data.get("exp", 0) + total_gained_exp
    char_data["level"] = char_data.get("level", 1)

    # レベルアップチェック
    rewards = check_level_up(char_data)

    # 報酬をユーザーのインベントリに付与する処理などをここで行う
    # ...

    return {
        "taste_type": taste_type,
        "is_first_time": is_first_time,
        "gained_exp": total_gained_exp,
        "current_level": char_data["level"],
        "rewards": rewards
    }
