import random
import discord
from discord import app_commands
from discord.ext import commands
from achievement import on_gamble_win
from database import user_data

# --------------------------------------------------
# ⚙️ 設定: コマンドの使用を許可するフォーラムチャンネルのID
# --------------------------------------------------
TARGET_FORUM_ID = 1550759772930838558

# ーーーーーーーーーーーーーーー
async def character_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    # 入力中の文字が含まれるキャラを検索して最大25件まで返す
    return [
        app_commands.Choice(name=char, value=char)
        for char in CHARACTER_CHOICES
        if current.lower() in char.lower()
    ][:25]

CHARACTER_CHOICES = [
    "サラ", "竹村しえら", 
]

# --------------------------------------------------
# 💬 キャラクターごとの「累計負け数に応じた」セリフ設定
# --------------------------------------------------    
CHAR_REACTIONS = {
    "サラ": {
        1: {
            "item": "耳の謎アクセ",
            "quote": "「ふん、まだ一回ですから。これくらいで勝った気になられちゃ困りますよ。」",
        },
        2: {
            "item": "上着",
            "quote": "「いや、いやまだ、あの、次で取り返せますから、こんなもの……」",
        },
        3: {
            "item": "セーター",
            "quote": "「つ、次こそ取り返せるから……」",
        },
        4: {
            "item": "シャツのボタンを外す",
            "quote": "「あ、あの……ボタンで勘弁してくれませんか……？；；」",
        },
        5: {
            "item": "シャツ",
            "quote": "「はい！ 脱げばいいんでしょ脱げば！！」",
        },
        6: {
            "item": "靴と靴下",
            "quote": "「な、なんか……世の中には足で興奮する人がいるとかいないとか……。……俺男ですよ…？」",
        },
        7: {
            "item": "ズボン",
            "quote": "「逆になんかイカサマやってるでしょあなた！！ ほらズボン！ はい！」",
        },
        8: {
            "item": "サラは何も脱がなかった！",
            "quote": "「こんな、こんな格好で集中できるとでも？！；；」",
        },
        9: {
            "item": "サラは何も脱がなかった！",
            "quote": "「いや、次は絶対俺が勝つので……。次負けたらもうあのほんと、なんでもするんで……。マジでこれは勘弁……」",
        },
        10: {
            "item": "？？？",
            "quote": "「……な、なんでもするって言った？ きき気のせいじゃないっすかねぇ…」",
        },
    },
    "竹村しえら": {
        1: {
            "item": "しえらは何も脱がなかった！",
            "quote": "「まだ負けたわけじゃないが？ ほら、次だ次。次やるぞ」",
        },
        2: {
            "item": "パーカー",
            "quote": "「何これ、賭けるものがなくなったら服賭けれんの……？ じゃあはい…パーカー……」",
        },
        3: {
            "item": "ネクタイ",
            "quote": "「え、つ、つぎ……？ じゃあ……ネクタイ……」",
        },
        4: {
            "item": "しえらは何も脱がなかった！",
            "quote": "「ぜぇっっったい嫌。あのね、次こそしえらさんが勝つもんでね。」",
        },
        5: {
            "item": "シャツのボタンを外す",
            "quote": "「マジで嫌……せめてパーカー返して……」",
        },
        6: {
            "item": "シャツ",
            "quote": "「はい、これでいい？？ 絶対こっち見んなよ殺すぞ」",
        },
        7: {
            "item": "靴と靴下",
            "quote": "「俺知ってるぞ、靴下食う変態がいるんだろ。やめろよ。食うなよ」",
        },
        8: {
            "item": "ズボン",
            "quote": "「えあの今までのことなかったことにしていいすか」",
        },
        9: {
            "item": "キャミソール",
            "quote": "「マジでこっち見んな。」",
        },
        10: {
            "item": "パンツ",
            "quote": "「………服、返してもらえないですか……？」",
        },
    },
}

# 登録のないキャラ用のデフォルト
DEFAULT_REACTIONS = {
    i: {
        "item": f"装備品 Part.{i}",
        "quote": f"「くっ……（{i}回目の敗北で装備を失った）」",
    }
    for i in range(1, 11)
}

# --------------------------------------------------
# 💬 キャラクターごとの「勝った時（正解した時）」の専用セリフ（ランダム）
# --------------------------------------------------
CHAR_WIN_QUOTES = {
    "サラ": [
        "「ほら見たことですか！ 俺の読みのほうが正確なんですよ！」",
        "「ふっふーん、調子いいっすね！ このまま連勝しちゃいますよ！」",
        "「よっしゃ！ この調子でどんどんいきましょう！」",
        "「当然の結果ですね。俺の頭脳を舐めないでください！」",
    ],
    "竹村しえら": [
        "「っは、当然だな。しえらさんを舐めるなよ」",
        "「おっ、また勝った。この調子で調子狂わせてやるからな」",
        "「いいぞ、このまま圧倒してやる……！」",
        "「へへっ、どうだ？ まだまだ甘いんじゃないの？」",
    ],
}

# 登録のないキャラ用のデフォルト勝利セリフ
DEFAULT_WIN_QUOTES = [
    "「よし！ 私の予想通りですね！」",
    "「ふふん、見事に当たりました！」",
    "「この調子でどんどんいきますよ！」",
]

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

        # --------------------------------------------------
        # 🎯 1. キャラの予想決定 & 5回以上負け時の「ヘマ（パニック）」処理
        # --------------------------------------------------
        # 基本の予想
        base_choice = random.choice(["HIGH", "LOW"])
        is_panic_hema = False

        # 5回以上負けている場合、50%の確率で動揺して判定ミス（逆を選ぶ）
        if self.char_losses >= 5 and random.random() < 0.50:
            char_choice = "LOW" if base_choice == "HIGH" else "HIGH"
            is_panic_hema = True
        else:
            char_choice = base_choice

        # 2. 次のカードを引く
        next_card = random.randint(1, 13)
        while next_card == self.current_card:
            next_card = random.randint(1, 13)

        # 3. 正解判定
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
            
            # 🏆 ターン毎のGM正解時に実績カウント＆解除チェック
            u_data = user_data.setdefault(self.user_id, {})
            await on_gamble_win(interaction, u_data)
            
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
            # ⭕ キャラの勝利時：専用セリフリストからランダムに1つ選択
            win_quotes = CHAR_WIN_QUOTES.get(self.char_name, DEFAULT_WIN_QUOTES)
            quote = random.choice(win_quotes)
            
            # ヘマしそうになったけど奇跡的に当たった場合の演出（お好みで）
            if is_panic_hema:
                reaction_text = f"\n\n💦 **{self.char_name}**: （あせって押し間違えたのに当たった…！？）\n✨ **{self.char_name}**: {quote}"
            else:
                reaction_text = f"\n\n✨ **{self.char_name}**: {quote}"
        else:
            char_dict = CHAR_REACTIONS.get(self.char_name, DEFAULT_REACTIONS)
            data = char_dict.get(
                self.char_losses,
                {"item": "???", "quote": "「くっ……！」"}
            )

            stripped_item = data["item"]
            quote = data["quote"]

            hema_notice = ""
            if is_panic_hema:
                hema_notice = f"\n😰 **（{self.char_name} は極度の緊張でパニックになり、焦って予想を言い間違えてしまった！）**"

            reaction_text = (
                f"{hema_notice}\n\n"
                f"⚠️ **{self.char_name} が脱いだもの**: **【 {stripped_item} 】**\n"
                f"**{self.char_name}（通算 {self.char_losses} 回目の失敗）**: {quote}"
            )

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
    @app_commands.describe(char_name="勝負を挑むキャラクターを選択してください")
    @app_commands.autocomplete(char_name=character_autocomplete)  # 👈 引数名 char_name に合わせる
    async def gamble_command(
        self, interaction: discord.Interaction, char_name: str
    ):
        # リストにない文字が直接入力された場合のガード
        if char_name not in CHARACTER_CHOICES:
            await interaction.response.send_message(
                "リストにあるキャラクターを選択してください！", ephemeral=True
            )
            return

        channel = interaction.channel

        # --------------------------------------------------
        # 🎯 指定されたフォーラムチャンネル（またはその中のスレッド）か判定
        # --------------------------------------------------
        current_forum_id = (
            channel.parent_id
            if isinstance(channel, discord.Thread)
            else channel.id
        )

        # 指定フォーラムチェック
        if current_forum_id != TARGET_FORUM_ID:
            await interaction.response.send_message(
                "❌ このコマンドは指定されたフォーラムチャンネルでのみ使用できます！",
                ephemeral=True,
            )
            return

        # ゲームスタート
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
