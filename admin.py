import time
import discord
from discord import app_commands
from database import user_data, save_data, GACHA_POOL, get_user_profile
from battle import execute_battle

# 👑 あなたのDiscordユーザーID（数値）
ADMIN_ID = 837631984280666162

def is_admin():
    """管理者チェック用のデコレータ"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ このコマンドは管理者専用です。", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)


# --------------------------------------------------
# 🔄 キャラクターデータ再計算ロジック
# --------------------------------------------------
def recalculate_all_characters() -> tuple[int, int]:
    """全ユーザーのキャラクターデータを再計算する処理"""
    updated_users = 0
    updated_chars = 0

    for user_id, u_data in user_data.items():
        characters = u_data.get("characters", [])
        if not characters:
            continue

        for char in characters:
            # GACHA_POOL から基礎データを取得
            template = next((c for c in GACHA_POOL if c["name"] == char["name"]), None)
            if not template:
                continue

            # 1. レベルによる上昇分（※プロジェクトの成長計算式に合わせて調整してください）
            level = char.get("level", 1)
            level_hp_bonus = (level - 1) * 10
            level_atk_bonus = (level - 1) * 2

            # 2. ランクアップ（★）による上昇分
            base_rarity = template.get("rarity", "★3")
            current_rarity = char.get("rarity", base_rarity)

            rarity_map = {"★1": 1, "★2": 2, "★3": 3, "★4": 4, "★5": 5}
            rank_diff = max(0, rarity_map.get(current_rarity, 3) - rarity_map.get(base_rarity, 3))

            base_hp = template.get("hp", 100)
            base_atk = template.get("atk", 10)

            rank_hp_bonus = int(base_hp * 0.20) * rank_diff
            rank_atk_bonus = int(base_atk * 0.20) * rank_diff

            # 3. 再計算して上書き
            correct_hp = base_hp + level_hp_bonus + rank_hp_bonus
            correct_atk = base_atk + level_atk_bonus + rank_atk_bonus

            char["hp"] = correct_hp
            if "max_hp" in char:
                char["max_hp"] = correct_hp
            char["atk"] = correct_atk

            updated_chars += 1
        updated_users += 1

    save_data()
    return updated_users, updated_chars


# --------------------------------------------------
# 🔄 4. キャラステータス一括再計算コマンド
# --------------------------------------------------
@app_commands.command(name="admin_recalculate", description="【管理者】全ユーザーのキャラステータスを再計算・修正します")
@is_admin()
async def admin_recalculate(interaction: discord.Interaction):
    # 処理が長引く可能性があるため応答を保留
    await interaction.response.defer(ephemeral=True)

    users_cnt, chars_cnt = recalculate_all_characters()

    embed = discord.Embed(
        title="🔄 キャラクターデータ再計算完了",
        description="全ユーザーのステータス再計算とデータの保存が正常に完了しました！",
        color=0x2ECC71
    )
    embed.add_field(name="対象ユーザー数", value=f"**{users_cnt}** 人", inline=True)
    embed.add_field(name="更新キャラ数", value=f"**{chars_cnt}** 体", inline=True)

    await interaction.followup.send(embed=embed, ephemeral=True)


# --------------------------------------------------
# ✉️ メール配布機能（全体送信・個別送信・全取消）
# --------------------------------------------------

# 📢 1. 全体メール送信（キャラ添付対応）
@app_commands.command(name="admin_mail", description="【管理者】プレイヤー全体にメール・アイテム・キャラを配布します")
@is_admin()
async def admin_mail(
    interaction: discord.Interaction,
    mail_id: str,
    title: str,
    message: str,
    gold: int = 0,
    rainbow: int = 0,
    ticket: int = 0,
    char_name: str = None  # 👈 添付キャラ名（任意）
):
    if char_name:
        char_exists = any(c.get("name") == char_name for c in GACHA_POOL)
        if not char_exists:
            await interaction.response.send_message(
                f"❌ 指定されたキャラ `{char_name}` はガチャプールに存在しません。",
                ephemeral=True
            )
            return

    count = 0
    for u_id, u_info in user_data.items():
        if "mails" not in u_info:
            u_info["mails"] = []

        if not any(m["id"] == mail_id for m in u_info["mails"]):
            u_info["mails"].append({
                "id": mail_id,
                "title": title,
                "message": message,
                "gold": gold,
                "rainbow": rainbow,
                "ticket": ticket,
                "char_name": char_name,
                "claimed": False
            })
            count += 1

    save_data()

    attachments = []
    if gold > 0:
        attachments.append(f"{gold}G")
    if rainbow > 0:
        attachments.append(f"虹の欠片 {rainbow}個")
    if ticket > 0:
        attachments.append(f"ガチャチケ {ticket}枚")
    if char_name:
        attachments.append(f"👤 {char_name}")

    attachment_str = " / ".join(attachments) if attachments else "なし"

    await interaction.response.send_message(
        f"📧 **全体メールを一斉送信しました！**\n"
        f"・対象人数: {count} 人\n"
        f"・メールID: `{mail_id}`\n"
        f"・件名: {title}\n"
        f"・添付: {attachment_str}",
        ephemeral=True
    )


# ✉️ 2. 個人メール送信
@app_commands.command(name="admin_direct_mail", description="【管理者】特定ユーザーに個人メールを送信します")
@is_admin()
async def admin_direct_mail(
    interaction: discord.Interaction,
    target: discord.User,
    title: str,
    message: str,
    gold: int = 0,
    rainbow: int = 0,
    ticket: int = 0,
    char_name: str = None
):
    if char_name:
        char_exists = any(c.get("name") == char_name for c in GACHA_POOL)
        if not char_exists:
            await interaction.response.send_message(
                f"❌ 指定されたキャラ `{char_name}` はガチャプールに存在しません。",
                ephemeral=True
            )
            return

    u_info = user_data.get(target.id)
    if not u_info:
        await interaction.response.send_message("❌ 指定されたユーザーのデータが見つかりませんでした。", ephemeral=True)
        return

    if "mails" not in u_info:
        u_info["mails"] = []

    auto_mail_id = f"DM_{int(time.time())}"

    u_info["mails"].append({
        "id": auto_mail_id,
        "title": title,
        "message": message,
        "gold": gold,
        "rainbow": rainbow,
        "ticket": ticket,
        "char_name": char_name,
        "claimed": False
    })

    save_data()

    attachments = []
    if gold > 0:
        attachments.append(f"{gold}G")
    if rainbow > 0:
        attachments.append(f"虹の欠片 {rainbow}個")
    if ticket > 0:
        attachments.append(f"ガチャチケ {ticket}枚")
    if char_name:
        attachments.append(f"👤 {char_name}")

    attachment_str = " / ".join(attachments) if attachments else "なし"

    await interaction.response.send_message(
        f"📨 **{target.mention} へ個人メールを送信しました！**\n"
        f"・メールID: `{auto_mail_id}`\n"
        f"・件名: {title}\n"
        f"・添付: {attachment_str}",
        ephemeral=True
    )


# 🗑️ 3. メール取り消し
@app_commands.command(name="admin_cancel_mail", description="【管理者】誤送信したメールを取り消します（未受取分のみ）")
@is_admin()
async def admin_cancel_mail(interaction: discord.Interaction, mail_id: str):
    removed_count = 0
    for u_id, u_info in user_data.items():
        if "mails" in u_info:
            original_len = len(u_info["mails"])
            u_info["mails"] = [
                m for m in u_info["mails"] 
                if not (m["id"] == mail_id and not m.get("claimed", False))
            ]
            removed_count += (original_len - len(u_info["mails"]))

    save_data()
    await interaction.response.send_message(
        f"🗑️ **メールの取り消し処理が完了しました。**\n"
        f"・メールID: `{mail_id}`\n"
        f"・回収・削除数: {removed_count} 件（受取済みのものは回収されません）",
        ephemeral=True
    )


# 🛠 他ユーザーのデータも修正可能なコマンド
@app_commands.command(name="set_char_count", description="【管理者用】指定ユーザーのキャラ所持数（count）を直接変更します")
@is_admin()
async def set_char_count(
    interaction: discord.Interaction, 
    char_name: str, 
    count: int,
    target: discord.User = None
):
    target_user = target or interaction.user
    
    u_data = get_user_profile(target_user.id)
    chars = u_data.get("characters", [])
    
    target_char = next((c for c in chars if c["name"] == char_name), None)
    
    if not target_char:
        await interaction.response.send_message(
            f"❌ {target_user.mention} はキャラクター `{char_name}` を所持していません。", 
            ephemeral=True
        )
        return

    old_count = target_char.get("count", 1)
    
    target_char["count"] = max(1, count)
    target_char["limit_break"] = max(0, count - 1)
    target_char.pop("rank_up", None)

    save_data()
    
    lb_str = f"+{target_char['limit_break']}" if target_char['limit_break'] > 0 else "無凸"
    await interaction.response.send_message(
        f"✅ **{target_user.display_name}** さんの **{char_name}** を修正しました！\n"
        f"・所持数: `{old_count}` ➔ `{target_char['count']}`\n"
        f"・限界突破: `{lb_str}`",
        ephemeral=True
    )


# 🛠 レア度（★の数）を直接変更するコマンド
@app_commands.command(name="set_char_rarity", description="【管理者用】指定ユーザーのキャラのベースレア度（★）を変更します")
@is_admin()
async def set_char_rarity(
    interaction: discord.Interaction, 
    char_name: str, 
    rarity: int,
    target: discord.User = None
):
    target_user = target or interaction.user
    u_data = get_user_profile(target_user.id)
    chars = u_data.get("characters", [])
    
    target_char = next((c for c in chars if c["name"] == char_name), None)
    
    if not target_char:
        await interaction.response.send_message(
            f"❌ {target_user.mention} はキャラクター `{char_name}` を所持していません。", 
            ephemeral=True
        )
        return

    old_rarity = target_char.get("rarity")
    
    target_char["rarity"] = rarity

    save_data()
    
    await interaction.response.send_message(
        f"✅ **{target_user.display_name}** さんの **{char_name}** のレア度を修正しました！\n"
        f"・元データ: `{old_rarity}`\n"
        f"・変更後: `★{rarity}`",
        ephemeral=True
    )


# --------------------------------------------------
# ⚔️ テストバトル機能
# --------------------------------------------------
@app_commands.command(name="admin_test_battle", description="【管理者】テストバトルを実行します")
@is_admin()
async def admin_test_battle(interaction: discord.Interaction):
    await execute_battle(interaction, is_event=False)


async def setup(bot):
    # コマンドをボットのツリーに登録
    bot.tree.add_command(admin_recalculate)  # 👈 再計算コマンドを追加
    bot.tree.add_command(admin_mail)
    bot.tree.add_command(admin_direct_mail)
    bot.tree.add_command(admin_cancel_mail)
    bot.tree.add_command(set_char_count)
    bot.tree.add_command(set_char_rarity)
    bot.tree.add_command(admin_test_battle)
