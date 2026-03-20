from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = (
    "📒 <b>Khata Bot — Command Guide</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"

    "💱 <b>Currency</b>\n"
    "  /setprice &lt;price&gt; — Set USDT rate\n"
    "  /price — Show current USDT rate\n"
    "  /convert &lt;amount&gt; &lt;inr/usdt&gt; — Convert currency\n\n"

    "💸 <b>Transactions</b>\n"
    "  /debit &lt;amount&gt; &lt;inr/usdt&gt; [note] — Record money you gave to group\n"
    "  /credit &lt;amount&gt; &lt;inr/usdt&gt; [note] — Record money you received from group\n\n"

    "📊 <b>Ledger</b>\n"
    "  /balance — Your balance with the group\n"
    "  /ledger — Your transaction history\n"
    "  /settle — Mark your balance as settled\n"
    "  /export — Export all transactions to CSV\n\n"

    "━━━━━━━━━━━━━━━━━━━━\n"
    "💡 Both INR & USDT shown in all responses"
)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    await msg.reply_text(HELP_TEXT, parse_mode="HTML")
