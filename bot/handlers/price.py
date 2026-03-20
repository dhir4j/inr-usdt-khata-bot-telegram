from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import set_price, get_price
from bot.utils.helpers import is_group_chat


async def setprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) != 1:
        await msg.reply_text(
            "❓ <b>Usage:</b> /setprice &lt;price&gt;\n"
            "📌 <b>Example:</b> /setprice 83.5",
            parse_mode="HTML",
        )
        return

    try:
        price = float(context.args[0])
        if price <= 0:
            raise ValueError
    except ValueError:
        await msg.reply_text("❌ Price must be a positive number.")
        return

    group_id = update.effective_chat.id
    set_price(group_id, price)

    await msg.reply_text(
        f"✅ <b>USDT Price Updated</b>\n\n"
        f"💱 <b>1 USDT = ₹{price}</b>",
        parse_mode="HTML",
    )


async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
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

    await msg.reply_text(
        f"📊 <b>Current Rate</b>\n\n"
        f"💱 <b>1 USDT = ₹{price}</b>",
        parse_mode="HTML",
    )
