import discord
from discord import app_commands
from database import user_data, save_data
from battle import run_battle

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
# ✉️ メール配布機能（送信・全取消）
# --------------------------------------------------
@app_commands.command(name="admin_mail", description="【管理者】プレイヤー全体にメール・アイテムを配布します")
@is_admin()
async def admin_mail(
    interaction: discord.Interaction,
    mail_id: str,
    title: str,
    message: str,
    gold: int = 0,
    rainbow: int = 0,
    ticket: int = 0
):
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
                "claimed": False
            })
            count += 1

    save_data()

    # --------------------------------------------------
    # 🎁 添付アイテムの表示文を作成（0のものは除外）
    # --------------------------------------------------
    attachments = []
    if gold > 0:
        attachments.append(f"{gold}G")
    if rainbow > 0:
        attachments.append(f"虹の欠片 {rainbow}個")
    if ticket > 0:
        attachments.append(f"ガチャチケ {ticket}枚")

    # 1つでも添付があれば「 / 」で繋ぎ、何もなければ「なし」にする
    attachment_str = " / ".join(attachments) if attachments else "なし"

    await interaction.response.send_message(
        f"📧 **メールを一斉送信しました！**\n"
        f"・対象人数: {count} 人\n"
        f"・メールID: `{mail_id}`\n"
        f"・件名: {title}\n"
        f"・添付: {attachment_str}",
        ephemeral=True
    )


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


# --------------------------------------------------
# ⚔️ テストバトル機能
# --------------------------------------------------
@app_commands.command(name="admin_test_battle", description="【管理者】テストバトルを実行します")
@is_admin()
async def admin_test_battle(interaction: discord.Interaction):
    # run_battle 自体が最初のメッセージ送信を行うため、直接呼び出します
    await run_battle(interaction)


async def setup(bot):
    # コマンドをボットのツリーに登録
    bot.tree.add_command(admin_mail)
    bot.tree.add_command(admin_cancel_mail)
    bot.tree.add_command(admin_test_battle)
