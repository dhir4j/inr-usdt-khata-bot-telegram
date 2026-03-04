from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import get_price
from bot.services.converter import inr_to_usdt, usdt_to_inr
from bot.utils.helpers import is_group_chat


async def convert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) != 2:
        await msg.reply_text(
            "❓ <b>Usage:</b> /convert &lt;amount&gt; &lt;inr/usdt&gt;\n\n"
            "📌 <b>Examples:</b>\n"
            "  /convert 1000 inr\n"
            "  /convert 10 usdt",
            parse_mode="HTML",
        )
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await msg.reply_text("❌ Amount must be a positive number.")
        return

    currency = context.args[1].lower()
    if currency not in ("inr", "usdt"):
        await msg.reply_text("❌ Currency must be <b>inr</b> or <b>usdt</b>.", parse_mode="HTML")
        return

    group_id = update.effective_chat.id
    price = get_price(group_id)

    if price <= 0:
        await msg.reply_text(
            "⚠️ Price not set yet.\n"
            "👉 Use /setprice &lt;price&gt; to set it.",
            parse_mode="HTML",
        )
        return

    if currency == "inr":
        converted = inr_to_usdt(amount, price)
        text = (
            f"🔄 <b>Conversion</b>\n\n"
            f"🇮🇳 ₹{amount:,.2f}  →  💵 {converted:,.2f} USDT\n\n"
            f"📊 Rate: 1 USDT = ₹{price}"
        )
    else:
        converted = usdt_to_inr(amount, price)
        text = (
            f"🔄 <b>Conversion</b>\n\n"
            f"💵 {amount:,.2f} USDT  →  🇮🇳 ₹{converted:,.2f}\n\n"
            f"📊 Rate: 1 USDT = ₹{price}"
        )

    await msg.reply_text(text, parse_mode="HTML")
