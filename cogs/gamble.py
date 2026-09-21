import random
import discord
from discord import app_commands
from discord.ext import commands

# --------------------------------------------------
# 💬 キャラクターごとの敗北（焦り・反応）メッセージ設定
# --------------------------------------------------
CHAR_REACTIONS = {
    "折原和也": [
        "「くっ……論理的には説明がつかないな……もう一度だ」",
        "「おいおい、GM……手加減って言葉を知らないのかい？」",
        "「冷や汗が出てきたな……これ以上負けるわけにはいかない」",
    ],
    "西谷しえら": [
        "「えっ嘘でしょ！？ GMちゃん強すぎない！？！？」",
        "「やばいやばい配信事故レベルで負けてるんだけど！！」",
        "「うぐぐ……リスナーに見せられない顔になっちゃう……！」",
    ],
    "DEFAULT": [
        "「くっ……負けたか……！」",
        "「GM、なかなかやるな……次は負けないぞ！」",
        "「うそだろ……もう後がないぞ……！？」",
    ],
}


# --------------------------------------------------
# 🃏 ハイアンドローのゲームView（UIとロジック）
# --------------------------------------------------
class HighAndLowView(discord.ui.View):

    def __init__(
        self, user_id: int, char_name: str, total_turns: int = 10
    ):
        super().__init__(timeout=300)  # 5分タイムアウト
        self.user_id = user_id
        self.char_name = char_name
        self.total_turns = total_turns

        self.current_turn = 1
        self.gm_wins = 0
        self.char_wins = 0

        # 最初のカードを引く (1〜13)
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
        # トランプ風表示用
        names = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return names.get(num, str(num))

    async def process_choice(
        self, interaction: discord.Interaction, choice: str
    ):
        await interaction.response.defer()

        # 次のカードを引く
        next_card = random.randint(1, 13)

        # あいこ（同じ数字）の場合はもう一度引き直す
        while next_card == self.current_card:
            next_card = random.randint(1, 13)

        # 勝敗判定
        is_high = next_card > self.current_card
        user_won = (choice == "high" and is_high) or (
            choice == "low" and not is_high
        )

        curr_str = self.get_card_display(self.current_card)
        next_str = self.get_card_display(next_card)

        # メッセージの組み立て
        result_title = ""
        reaction_text = ""

        if user_won:
            self.gm_wins += 1
            result_title = "⭕ GMの勝ち！"

            # キャラが負けた時のリアクションを取得
            reactions = CHAR_REACTIONS.get(
                self.char_name, CHAR_REACTIONS["DEFAULT"]
            )
            reaction_text = f"\n\n**{self.char_name}**: {random.choice(reactions)}"
        else:
            self.char_wins += 1
            result_title = f"❌ {self.char_name} の勝ち！"
            reaction_text = (
                f"\n\n**{self.char_name}**: 「ふふっ、GMの読みも甘いですね」"
            )

        # 10ターン終了チェック
        if self.current_turn >= self.total_turns:
            self.stop_game()

            # 最終結果判定
            if self.gm_wins > self.char_wins:
                final_msg = f"🏆 **勝負終了！ GMの勝利です！** ({self.gm_wins}勝 {self.char_wins}敗)"
            elif self.char_wins > self.gm_wins:
                final_msg = f"💀 **勝負終了！ {self.char_name} の勝利です…** ({self.gm_wins}勝 {self.char_wins}敗)"
            else:
                final_msg = f"⚖️ **勝負終了！ 引き分けです！** ({self.gm_wins}勝 {self.char_wins}敗)"

            embed = discord.Embed(
                title=f"🎲 ハイアンドロー対決 【最終結果】",
                description=(
                    f"**【Turn {self.current_turn}/{self.total_turns}】**\n"
                    f"前のカード: **[{curr_str}]** ➔ 新しいカード: **[{next_str}]**\n"
                    f"判定: **{result_title}**{reaction_text}\n\n"
                    f"-----------------------------------\n"
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
                f"前のカード: **[{curr_str}]** ➔ 開いたカード: **[{next_str}]**\n"
                f"判定: **{result_title}**{reaction_text}\n\n"
                f"===================================\n"
                f"**【Turn {self.current_turn}/{self.total_turns}】**\n"
                f"現在のカード: 🎴 **[{self.get_card_display(self.current_card)}]**\n\n"
                f"次のカードはこれより **HIGH** か **LOW** か？"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"現在の戦績: GM {self.gm_wins}勝 - {self.char_wins}勝 {self.char_name}"
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
        await self.process_choice(interaction, "high")

    @discord.ui.button(
        label="LOW (低い)",
        style=discord.ButtonStyle.danger,
        custom_id="btn_low",
    )
    async def low_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_choice(interaction, "low")


# --------------------------------------------------
# ⚙️ コマンド Cog 本体
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

        # ゲーム開始処理
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
                f"次のカードはこれより **HIGH** か **LOW** か？"
            ),
            color=discord.Color.gold(),
        )
        embed.set_footer(text="選択ボタンを押してゲームを進めてください。")

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(GambleCog(bot))
