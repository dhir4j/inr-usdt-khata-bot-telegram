from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import (
    get_price, add_transaction, get_net_balance_inr, GROUP_SENTINEL,
)
from bot.services.converter import convert_amount, inr_to_usdt
from bot.utils.helpers import is_group_chat, format_both

TYPE_META = {
    "debit":  ("📤", "Debit Recorded"),
    "credit": ("📥", "Credit Recorded"),
}


async def _record_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, txn_type: str):
    msg = update.effective_message
    if not msg:
        return

    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) < 2:
        await msg.reply_text(
            f"❓ <b>Usage:</b> /{txn_type} &lt;amount&gt; &lt;inr/usdt&gt; [note]\n"
            f"📌 <b>Example:</b> /{txn_type} 500 inr dinner",
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

    note = " ".join(context.args[2:]) if len(context.args) > 2 else ""

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id

    price = get_price(group_id)
    if price <= 0:
        await msg.reply_text(
            "⚠️ Price not set yet.\n"
            "👉 Use /setprice &lt;price&gt; to set it.",
            parse_mode="HTML",
        )
        return

    amount_inr, amount_usdt = convert_amount(amount, currency, price)

    add_transaction(group_id, caller_id, GROUP_SENTINEL, amount_inr, amount_usdt, txn_type, note)

    net_inr = get_net_balance_inr(group_id, caller_id, GROUP_SENTINEL)
    net_usdt = inr_to_usdt(abs(net_inr), price)

    icon, type_label = TYPE_META[txn_type]
    text = f"{icon} <b>{type_label}</b>\n━━━━━━━━━━━━━━\n"
    text += f"💰 {format_both(amount_inr, amount_usdt)}\n"
    if note:
        text += f"📝 {note}\n"

    text += "\n━━━━━━━━━━━━━━\n📊 <b>Your Balance with Group</b>\n"
    if net_inr > 0.01:
        text += f"✅ Group owes you\n💵 {format_both(net_inr, net_usdt)}"
    elif net_inr < -0.01:
        text += f"🔴 You owe group\n💵 {format_both(abs(net_inr), net_usdt)}"
    else:
        text += "⚪ All settled! Balance = ₹0"

    await msg.reply_text(text, parse_mode="HTML")


async def debit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _record_transaction(update, context, "debit")


async def credit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _record_transaction(update, context, "credit")
