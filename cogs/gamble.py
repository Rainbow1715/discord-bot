import random
import discord
from discord import app_commands
from discord.ext import commands

# --------------------------------------------------
# ⚙️ 設定: コマンドの使用を許可するフォーラムチャンネルのID
# --------------------------------------------------
# ※ Discordでフォーラムチャンネルを右クリックして「チャンネルIDをコピー」した数字を入れてください
TARGET_FORUM_ID = 1550759772930838558

# --------------------------------------------------
# 💬 キャラクターごとの「累計負け数に応じた」セリフ設定
# --------------------------------------------------
CHAR_REACTIONS = {
    "折原和也": {
        1: "「ふむ、1回目のミスか。まあ確率の偏りだな」",
        2: "「2連続で外すとは…計算に誤差があったようだ」",
        3: "「くっ……論理的には説明がつかないな……」",
        4: "「4回目…おいおいGM、手加減って言葉を知らないのかい？」",
        5: "「半分終わってこのザマか…冷や汗が出てきたな」",
        6: "「……笑えないぞ。僕のシミュレーションが崩れている」",
        7: "「嘘だろ！？ なぜ裏目ばかり出るんだ！」",
        8: "「心が乱れる…落ち着け…落ち着くんだ僕…」",
        9: "「あとがない…頼む、次こそは正解であってくれ…！」",
        10: "「完敗だ……僕の負けだよ、GM……」",
    },
    "西谷しえら": {
        1: "「あれっ！？ 違った！？ ま、まあ最初はウォームアップだしね！」",
        2: "「えっ2回目！？ GMちゃん強すぎない！？」",
        3: "「やばいやばい、リスナーに見せられない顔になってきた…！」",
        4: "「ちょっと待って！ カード絶対仕込んでるでしょ！？」",
        5: "「うぐぐ……半分負けてるんだけどどういうこと〜〜！？」",
        6: "「だ、誰か助けてー！ GMちゃんが容惹ないよ〜！」",
        7: "「もうヤダ〜〜！ 次外したら泣くからね！？」",
        8: "「たのむうううう！ 当たってくれええええ！！」",
        9: "「ひ、配信事故です…これ完全に配信事故です……」",
        10: "「うわああああん！！ GMちゃんのバカーー！！」",
    },
}

DEFAULT_REACTIONS = {
    1: "「くっ、外したか……まあ次だ！」",
    2: "「2回目……焦るな、まだいける」",
    3: "「うそだろ、また外れたのか！？」",
    4: "「GM、なかなかやるな……！」",
    5: "「くそっ、もう後がないぞ……！？」",
    6: "「冷や汗が止まらない……」",
    7: "「おいおい冗談だろ！？」",
    8: "「頼む……当たってくれ……！」",
    9: "「もう崖っぷちだ……！」",
    10: "「完敗だ……参りました……」",
}


# --------------------------------------------------
# 🃏 ハイアンドロー View
# --------------------------------------------------
class HighAndLowView(discord.ui.View):

    def __init__(
        self, user_id: int, char_name: str, total_turns: int = 10
    ):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.char_name = char_name
        self.total_turns = total_turns

        self.current_turn = 1
        self.gm_wins = 0  # GMが当てた回数
        self.char_wins = 0  # キャラが当てた回数
        self.char_losses = 0  # キャラが外した回数（リアクション判定用）

        self.current_card = random.randint(1, 13)

    async def interaction_check(
        self, interaction: discord.Interaction
    ) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ ゲームマスター（勝負を挑んだ本人）しか操作できません！",
                ephemeral=True,
            )
            return False
        return True

    def get_card_display(self, num: int) -> str:
        names = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return names.get(num, str(num))

    async def process_turn(
        self, interaction: discord.Interaction, gm_choice: str
    ):
        await interaction.response.defer()

        # 1. キャラの予想を決定（確率でHIGH/LOWを選択）
        # ※数字が小さい時はHIGH、大きい時はLOWを選びやすくするAI風にしても面白いです
        char_choice = random.choice(["HIGH", "LOW"])

        # 2. 次のカードを引く
        next_card = random.randint(1, 13)
        while next_card == self.current_card:
            next_card = random.randint(1, 13)

        # 3. 正解判定 (HIGHかLOWか)
        actual_result = (
            "HIGH" if next_card > self.current_card else "LOW"
        )

        gm_correct = gm_choice == actual_result
        char_correct = char_choice == actual_result

        curr_str = self.get_card_display(self.current_card)
        next_str = self.get_card_display(next_card)

        # GMの得点・キャラの得点/負け数の計算
        if gm_correct:
            self.gm_wins += 1
        if char_correct:
            self.char_wins += 1
        else:
            self.char_losses += 1

        # 表示テキストの組み立て
        gm_choice_str = "HIGH ⬆️" if gm_choice == "HIGH" else "LOW ⬇️"
        char_choice_str = "HIGH ⬆️" if char_choice == "HIGH" else "LOW ⬇️"

        gm_status = "⭕ 正解！" if gm_correct else "❌ 不正解…"
        char_status = "⭕ 正解！" if char_correct else "❌ 不正解…"

        reaction_text = ""
        if char_correct:
            reaction_text = (
                f"\n\n**{self.char_name}**: 「よし！ 私の予想通りですね！」"
            )
        else:
            # キャラの負け（ミス）回数に応じた段階的セリフ
            char_dict = CHAR_REACTIONS.get(
                self.char_name, DEFAULT_REACTIONS
            )
            reaction_quote = char_dict.get(
                self.char_losses,
                DEFAULT_REACTIONS.get(
                    self.char_losses, "「くっ……！」"
                ),
            )
            reaction_text = f"\n\n**{self.char_name}（累計 {self.char_losses} 回目の失敗）**: {reaction_quote}"

        # 10ターン終了チェック
        if self.current_turn >= self.total_turns:
            self.stop_game()

            if self.gm_wins > self.char_wins:
                final_msg = f"🏆 **勝負終了！ GMの勝利です！** (GM: {self.gm_wins}勝 / {self.char_name}: {self.char_wins}勝)"
            elif self.char_wins > self.gm_wins:
                final_msg = f"💀 **勝負終了！ {self.char_name} の勝利です！** (GM: {self.gm_wins}勝 / {self.char_name}: {self.char_wins}勝)"
            else:
                final_msg = f"⚖️ **勝負終了！ 引き分けです！** (両者 {self.gm_wins}勝)"

            embed = discord.Embed(
                title=f"🎲 ハイアンドロー対決 【最終結果】",
                description=(
                    f"**【Turn {self.current_turn}/{self.total_turns}】**\n"
                    f"前のカード: **[{curr_str}]** ➔ 開いたカード: **[{next_str}]** （正解: {actual_result}）\n\n"
                    f"👑 **GMの予想**: {gm_choice_str} （{gm_status}）\n"
                    f"👤 **{self.char_name} の予想**: {char_choice_str} （{char_status}）"
                    f"{reaction_text}\n\n"
                    f"===================================\n"
                    f"{final_msg}"
                ),
                color=discord.Color.gold(),
            )
            await interaction.followup.edit_message(
                message_id=interaction.message.id, embed=embed, view=None
            )
            return

        # 次のターンへ継続
        self.current_turn += 1
        self.current_card = next_card

        embed = discord.Embed(
            title=f"🎲 {self.char_name} とのハイアンドロー対決",
            description=(
                f"**【Turn {self.current_turn - 1}/{self.total_turns} の結果】**\n"
                f"前のカード: **[{curr_str}]** ➔ 開いたカード: **[{next_str}]** （正解: {actual_result}）\n\n"
                f"👑 **GMの予想**: {gm_choice_str} （{gm_status}）\n"
                f"👤 **{self.char_name} の予想**: {char_choice_str} （{char_status}）"
                f"{reaction_text}\n\n"
                f"===================================\n"
                f"**【Turn {self.current_turn}/{self.total_turns}】**\n"
                f"現在のカード: 🎴 **[{self.get_card_display(self.current_card)}]**\n\n"
                f"GM、次のカードはこれより **HIGH** か **LOW** か選んでください！"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"現在の的中数 ➔ GM: {self.gm_wins}勝 | {self.char_name}: {self.char_wins}勝 (失敗 {self.char_losses}回)"
        )

        await interaction.followup.edit_message(
            message_id=interaction.message.id, embed=embed, view=self
        )

    def stop_game(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(
        label="HIGH (高い)",
        style=discord.ButtonStyle.primary,
        custom_id="btn_high",
    )
    async def high_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_turn(interaction, "HIGH")

    @discord.ui.button(
        label="LOW (低い)",
        style=discord.ButtonStyle.danger,
        custom_id="btn_low",
    )
    async def low_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_turn(interaction, "LOW")


# --------------------------------------------------
# ⚙️ コマンド Cog
# --------------------------------------------------
class GambleCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="gamble",
        description="【指定フォーラム限定】指名したキャラと10ターンのハイ＆ロー対決を行います",
    )
    @app_commands.describe(char_name="勝負を挑むキャラクターの名前")
    async def gamble_command(
        self, interaction: discord.Interaction, char_name: str
    ):
        channel = interaction.channel

        # --------------------------------------------------
        # 🎯 指定されたフォーラムチャンネル（またはその中のスレッド）か判定
        # --------------------------------------------------
        # 1. チャンネル本体のIDを取得（スレッドの中なら親チャンネルのID、直下ならそのもののID）
        current_forum_id = (
            channel.parent_id
            if isinstance(channel, discord.Thread)
            else channel.id
        )

        # 2. 指定されたフォーラムIDと一致するかチェック
        if current_forum_id != TARGET_FORUM_ID:
            await interaction.response.send_message(
                "❌ このコマンドは指定されたフォーラムチャンネルでのみ使用できます！",
                ephemeral=True,
            )
            return

        # --------------------------------------------------
        # ⭕ IDが一致した場合のみゲームを開始
        # --------------------------------------------------
        view = HighAndLowView(
            user_id=interaction.user.id, char_name=char_name
        )

        embed = discord.Embed(
            title=f"🎲 {char_name} とのハイアンドロー対決が幕を開けた！",
            description=(
                f"**GM（ゲームマスター）**: {interaction.user.mention}\n"
                f"**対戦相手**: {char_name}\n\n"
                f"**【Turn 1/10】**\n"
                f"最初のカード: 🎴 **[{view.get_card_display(view.current_card)}]**\n\n"
                f"GMよ、次のカードはこれより **HIGH** か **LOW** か予測してください！"
            ),
            color=discord.Color.gold(),
        )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(GambleCog(bot))
