import random
import discord
from discord import app_commands
from discord.ext import commands

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
        6: "「だ、誰か助けてー！ GMちゃんが容赦ないよ〜！」",
        7: "「もうヤダ〜〜！ 次外したら泣くからね！？」",
        8: "「たのむうううう！ 当たってくれええええ！！」",
        9: "「ひ、配信事故です…これ完全に配信事故です……」",
        10: "「うわああああん！！ GMちゃんのバカーー！！」",
    },
}

# 設定がないキャラ・回数用のデフォルトセリフ
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
        self.gm_wins = 0  # GMの勝ち数（＝キャラの負け数）
        self.char_wins = 0  # キャラの勝ち数

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
        self, interaction: discord.Interaction, char_choice: str
    ):
        await interaction.response.defer()

        # 次のカードを引く
        next_card = random.randint(1, 13)
        while next_card == self.current_card:
            next_card = random.randint(1, 13)

        # 実際の結果（HIGHかLOWか）
        actual_result = (
            "HIGH" if next_card > self.current_card else "LOW"
        )
        char_won = char_choice == actual_result

        curr_str = self.get_card_display(self.current_card)
        next_str = self.get_card_display(next_card)

        # メッセージ構築
        choice_str = "HIGH ⬆️" if char_choice == "HIGH" else "LOW ⬇️"

        if char_won:
            self.char_wins += 1
            result_title = f"⭕ {self.char_name} の予想的中！"
            reaction_text = (
                f"\n\n**{self.char_name}**: 「よし！ 予想通りですね！」"
            )
        else:
            self.gm_wins += 1  # キャラの負け数をカウント
            result_title = f"❌ {self.char_name} は不正解！（GMのポイント）"

            # 負けた回数に応じた段階的セリフを取得
            char_dict = CHAR_REACTIONS.get(
                self.char_name, DEFAULT_REACTIONS
            )
            reaction_quote = char_dict.get(
                self.gm_wins,
                DEFAULT_REACTIONS.get(
                    self.gm_wins, "「くっ……！」"
                ),
            )

            reaction_text = f"\n\n**{self.char_name}（累計 {self.gm_wins} 回目の敗北）**: {reaction_quote}"

        # 10ターン終了チェック
        if self.current_turn >= self.total_turns:
            self.stop_game()

            if self.gm_wins > self.char_wins:
                final_msg = f"🏆 **勝負終了！ GMの勝利です！** ({self.gm_wins}敗させて追い詰めました！)"
            elif self.char_wins > self.gm_wins:
                final_msg = f"💀 **勝負終了！ {self.char_name} の勝利です！** ({self.char_wins}勝達成)"
            else:
                final_msg = f"⚖️ **勝負終了！ 引き分けです！** ({self.char_wins}勝 {self.gm_wins}敗)"

            embed = discord.Embed(
                title=f"🎲 ハイアンドロー対決 【最終結果】",
                description=(
                    f"**【Turn {self.current_turn}/{self.total_turns}】**\n"
                    f"現在のカード: **[{curr_str}]**\n"
                    f"👉 **{self.char_name}** の選択: **{choice_str}**\n"
                    f"開いたカード: **[{next_str}]** （正解: {actual_result}）\n\n"
                    f"判定: **{result_title}**{reaction_text}\n\n"
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
                f"前のカード: **[{curr_str}]**\n"
                f"👉 **{self.char_name}** は **{choice_str}** を選択！\n"
                f"開いたカード: **[{next_str}]** （正解: {actual_result}）\n"
                f"判定: **{result_title}**{reaction_text}\n\n"
                f"===================================\n"
                f"**【Turn {self.current_turn}/{self.total_turns}】**\n"
                f"現在のカード: 🎴 **[{self.get_card_display(self.current_card)}]**\n\n"
                f"GMよ、**{self.char_name}** にどちらを選ばせますか？（または選択を見守りますか？）"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"現在の戦績: {self.char_name} {self.char_wins}成功 / GM {self.gm_wins}失敗（キャラ負け）"
        )

        await interaction.followup.edit_message(
            message_id=interaction.message.id, embed=embed, view=self
        )

    def stop_game(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(
        label="キャラに HIGH を選ばせる",
        style=discord.ButtonStyle.primary,
    )
    async def high_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_turn(interaction, "HIGH")

    @discord.ui.button(
        label="キャラに LOW を選ばせる",
        style=discord.ButtonStyle.danger,
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
        description="【フォーラム限定】指名したキャラと10ターンのハイ＆ロー対決を行います",
    )
    @app_commands.describe(char_name="勝負を挑むキャラクターの名前")
    async def gamble_command(
        self, interaction: discord.Interaction, char_name: str
    ):
        # 🛡️ フォーラム判定
        channel = interaction.channel
        is_forum_thread = (
            isinstance(channel, discord.Thread)
            and channel.parent
            and channel.parent.type == discord.ChannelType.forum
        )
        is_forum_direct = channel.type == discord.ChannelType.forum

        if not (is_forum_thread or is_forum_direct):
            await interaction.response.send_message(
                "❌ このコマンドはフォーラムチャンネル（またはフォーラム内のスレッド）でのみ使用できます！",
                ephemeral=True,
            )
            return

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
                f"**{char_name}** に HIGH か LOW のどちらを選ばせますか？"
            ),
            color=discord.Color.gold(),
        )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(GambleCog(bot))
