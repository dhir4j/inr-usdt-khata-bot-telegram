from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = (
    "📒 <b>Khata Bot — Command Guide</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"

    "💱 <b>Currency</b>\n"
    "  /setprice &lt;price&gt; — Set USDT rate <i>(admin)</i>\n"
    "  /price — Show current USDT rate\n"
    "  /convert &lt;amount&gt; &lt;inr/usdt&gt; — Convert currency\n\n"

    "👥 <b>Users</b>\n"
    "  /add @user — Add user to ledger <i>(admin)</i>\n"
    "  /del @user — Remove user <i>(admin)</i>\n"
    "  /users — Show all balances\n\n"

    "💸 <b>Transactions</b>\n"
    "  /debit @user &lt;amount&gt; &lt;inr/usdt&gt; [note]\n"
    "  /credit @user &lt;amount&gt; &lt;inr/usdt&gt; [note]\n"
    "  /salary @user &lt;amount&gt; &lt;inr/usdt&gt; [note]\n\n"

    "📊 <b>Ledger</b>\n"
    "  /balance @user — Balance summary\n"
    "  /ledger @user — Full transaction history\n"
    "  /settle @user — Mark balance as settled\n"
    "  /export — Export all transactions to CSV\n"
    "  /export @user — Export transactions with a user\n\n"

    "━━━━━━━━━━━━━━━━━━━━\n"
    "💡 Both INR & USDT shown in all responses"
)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    await msg.reply_text(HELP_TEXT, parse_mode="HTML")
