from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import (
    get_price, get_user, get_user_by_username,
    add_transaction, get_net_balance_inr, add_user,
)
from bot.services.converter import convert_amount, inr_to_usdt
from bot.utils.helpers import (
    is_group_chat, is_group_admin, parse_username, format_both,
)

# Maps txn_type → (icon, label)
TYPE_META = {
    "debit":  ("📤", "Debit Recorded"),
    "credit": ("📥", "Credit Recorded"),
    "salary": ("💼", "Salary Recorded"),
}


async def _record_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, txn_type: str):
    msg = update.effective_message
    if not msg:
        return

    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) < 3:
        await msg.reply_text(
            f"❓ <b>Usage:</b> /{txn_type} @user &lt;amount&gt; &lt;inr/usdt&gt; [note]\n"
            f"📌 <b>Example:</b> /{txn_type} @rahul 500 inr dinner",
            parse_mode="HTML",
        )
        return

    username = parse_username(context.args[0])
    if not username:
        await msg.reply_text("❌ Please provide a valid @username.")
        return

    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await msg.reply_text("❌ Amount must be a positive number.")
        return

    currency = context.args[2].lower()
    if currency not in ("inr", "usdt"):
        await msg.reply_text("❌ Currency must be <b>inr</b> or <b>usdt</b>.", parse_mode="HTML")
        return

    note = " ".join(context.args[3:]) if len(context.args) > 3 else ""

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

    target = get_user_by_username(group_id, username)
    if not target:
        await msg.reply_text(
            f"❌ @{username} is not in the ledger.\n"
            f"👉 Add them first with /add @{username}",
        )
        return

    target_id = target["telegram_user_id"]

    caller_username = update.effective_user.username or ""
    caller_first_name = update.effective_user.first_name or caller_username
    caller_user = get_user(group_id, caller_id, caller_username)
    if not caller_user:
        if await is_group_admin(update):
            add_user(group_id, caller_id, caller_username, caller_first_name)
            caller_user = get_user(group_id, caller_id)
        else:
            await msg.reply_text(
                "🚫 You are not in the ledger.\n"
                "👉 Ask an admin to add you with /add."
            )
            return

    if target_id == caller_id:
        await msg.reply_text("❌ You cannot record a transaction with yourself.")
        return

    amount_inr, amount_usdt = convert_amount(amount, currency, price)

    # salary is stored as debit in the DB; the note carries the label
    db_type = "debit" if txn_type == "salary" else txn_type
    if txn_type == "salary" and not note:
        note = "Salary"

    add_transaction(group_id, caller_id, target_id, amount_inr, amount_usdt, db_type, note)

    net_inr = get_net_balance_inr(group_id, caller_id, target_id)
    net_usdt = inr_to_usdt(abs(net_inr), price)

    target_name = (target["first_name"] or target["username"]).title()
    icon, type_label = TYPE_META.get(txn_type, ("💸", "Transaction Recorded"))

    text = f"{icon} <b>{type_label}</b>\n━━━━━━━━━━━━━━\n"
    text += f"👤 @{target['username']}\n"
    text += f"💰 {format_both(amount_inr, amount_usdt)}\n"
    if note:
        text += f"📝 {note}\n"

    text += "\n━━━━━━━━━━━━━━\n📊 <b>Balance</b>\n"
    if net_inr > 0.01:
        text += f"✅ {target_name} owes you\n💵 {format_both(net_inr, net_usdt)}"
    elif net_inr < -0.01:
        text += f"🔴 You owe {target_name}\n💵 {format_both(abs(net_inr), net_usdt)}"
    else:
        text += "⚪ All settled! Balance = ₹0"

    await msg.reply_text(text, parse_mode="HTML")


async def debit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _record_transaction(update, context, "debit")


async def credit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _record_transaction(update, context, "credit")


async def salary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _record_transaction(update, context, "salary")
