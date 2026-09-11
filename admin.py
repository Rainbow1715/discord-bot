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
    # キャラ名が指定されている場合、ガチャプールに存在するかチェック
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
                "char_name": char_name,  # 👈 キャラ添付
                "claimed": False
            })
            count += 1

    save_data()

    # 🎁 添付表示文の作成
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
    # キャラ名チェック
    if char_name:
        char_exists = any(c.get("name") == char_name for c in GACHA_POOL)
        if not char_exists:
            await interaction.response.send_message(
                f"❌ 指定されたキャラ `{char_name}` はガチャプールに存在しません。",
                ephemeral=True
            )
            return

    # 対象ユーザーのデータ取得
    u_info = user_data.get(target.id)
    if not u_info:
        await interaction.response.send_message("❌ 指定されたユーザーのデータが見つかりませんでした。", ephemeral=True)
        return

    if "mails" not in u_info:
        u_info["mails"] = []

    # 一意のメールIDを自動生成
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


# 🛠 4. 限界突破修正コマンド
@app_commands.command(name="fix_limit", description="【管理者用】指定ユーザーのキャラデータを強制修正＆確認")
@is_admin()
async def fix_limit(interaction: discord.Interaction):
    u_data = get_user_profile(interaction.user.id)
    chars = u_data.get("characters", [])
    
    logs = []
    for c in chars:
        old_count = c.get("count")
        old_lb = c.get("limit_break")
        
        # 正しい limit_break を再計算
        real_count = c.get("count", 1)
        c["limit_break"] = max(0, real_count - 1)
        
        # 不要な旧キーを削る
        c.pop("rank_up", None)
        
        logs.append(f"・{c['name']}: count={old_count} -> {real_count} | lb={old_lb} -> {c['limit_break']}")

    save_data()
    
    msg = "\n".join(logs[:10])
    await interaction.response.send_message(
        f"🛠 **修正ログ（一部）:**\n{msg}\n\n✅ データを強制上書き・保存しました！",
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
    bot.tree.add_command(admin_mail)
    bot.tree.add_command(admin_direct_mail)
    bot.tree.add_command(admin_cancel_mail)
    bot.tree.add_command(fix_limit)  # 👈 ここに追加
    bot.tree.add_command(admin_test_battle)
