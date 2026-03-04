import math

from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import (
    get_price, get_user, get_user_by_username,
    get_balance, get_net_balance_inr,
    get_transactions, count_transactions,
    add_transaction,
)
from bot.services.converter import inr_to_usdt
from bot.utils.helpers import (
    is_group_chat, parse_username, format_both,
)
from bot.keyboards.pagination import ledger_pagination_keyboard

ITEMS_PER_PAGE = 10

TXN_ICONS = {
    "debit":  "📤",
    "credit": "📥",
    "settle": "🤝",
    "salary": "💼",
}


def _build_ledger_text(transactions, target_username: str, page: int, total_pages: int) -> str:
    lines = [
        f"📒 <b>Ledger with @{target_username}</b>",
        f"📄 Page {page} / {total_pages}\n",
    ]

    for i, txn in enumerate(transactions, start=(page - 1) * ITEMS_PER_PAGE + 1):
        txn_type = txn["type"]
        icon = TXN_ICONS.get(txn_type, "💸")
        label = txn_type.title()
        amount_inr = txn["amount_inr"]
        amount_usdt = txn["amount_usdt"]
        note = txn["note"] or ""
        date = txn["created_at"][:10] if txn["created_at"] else ""

        lines.append(f"{icon} <b>#{i} — {label}</b>")
        lines.append(f"   💰 {format_both(amount_inr, amount_usdt)}")
        if note:
            lines.append(f"   📝 {note}")
        if date:
            lines.append(f"   📅 {date}")
        lines.append("")

    return "\n".join(lines).strip()


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) != 1:
        await msg.reply_text(
            "❓ <b>Usage:</b> /balance @username",
            parse_mode="HTML",
        )
        return

    username = parse_username(context.args[0])
    if not username:
        await msg.reply_text("❌ Please provide a valid @username.")
        return

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id
    price = get_price(group_id)

    target = get_user_by_username(group_id, username)
    if not target:
        await msg.reply_text(f"❌ @{username} is not in the ledger.")
        return

    target_id = target["telegram_user_id"]

    if target_id == caller_id:
        await msg.reply_text("❌ You cannot check balance with yourself.")
        return

    bal = get_balance(group_id, caller_id, target_id)
    gave_inr    = bal["gave_inr"]
    received_inr = bal["received_inr"]
    net_inr     = bal["net_inr"]

    gave_usdt     = inr_to_usdt(gave_inr, price)     if price > 0 else 0
    received_usdt = inr_to_usdt(received_inr, price) if price > 0 else 0
    net_usdt      = inr_to_usdt(abs(net_inr), price) if price > 0 else 0

    target_name = (target["first_name"] or target["username"]).title()

    if net_inr > 0.01:
        status_line = f"✅ <b>{target_name} owes you</b>\n💰 {format_both(net_inr, net_usdt)}"
    elif net_inr < -0.01:
        status_line = f"🔴 <b>You owe {target_name}</b>\n💰 {format_both(abs(net_inr), net_usdt)}"
    else:
        status_line = "⚪ <b>All settled!</b>  Balance = ₹0"

    text = (
        f"📊 <b>Balance with @{target['username']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📤 You gave:     {format_both(gave_inr, gave_usdt)}\n"
        f"📥 You received: {format_both(received_inr, received_usdt)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{status_line}"
    )

    await msg.reply_text(text, parse_mode="HTML")


async def ledger_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) != 1:
        await msg.reply_text(
            "❓ <b>Usage:</b> /ledger @username",
            parse_mode="HTML",
        )
        return

    username = parse_username(context.args[0])
    if not username:
        await msg.reply_text("❌ Please provide a valid @username.")
        return

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id

    target = get_user_by_username(group_id, username)
    if not target:
        await msg.reply_text(f"❌ @{username} is not in the ledger.")
        return

    target_id = target["telegram_user_id"]

    total = count_transactions(group_id, caller_id, target_id)
    if total == 0:
        await msg.reply_text(
            f"📭 No transactions found with @{username}.",
        )
        return

    total_pages = math.ceil(total / ITEMS_PER_PAGE)
    txns = get_transactions(group_id, caller_id, target_id, limit=ITEMS_PER_PAGE, offset=0)

    text = _build_ledger_text(txns, target["username"], 1, total_pages)
    keyboard = ledger_pagination_keyboard(1, total_pages, caller_id, target_id, group_id)

    await msg.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def ledger_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("ledger:"):
        return

    parts = data.split(":")
    if len(parts) != 5:
        return

    _, group_id_str, user_a_str, user_b_str, page_str = parts

    try:
        group_id = int(group_id_str)
        user_a   = int(user_a_str)
        user_b   = int(user_b_str)
        page     = int(page_str)
    except ValueError:
        return

    if query.from_user.id != user_a:
        await query.answer("🚫 This is not your ledger.", show_alert=True)
        return

    target = get_user(group_id, user_b)
    if not target:
        await query.edit_message_text("❌ User not found in ledger.")
        return

    total = count_transactions(group_id, user_a, user_b)
    total_pages = math.ceil(total / ITEMS_PER_PAGE)

    if page < 1 or page > total_pages:
        return

    offset = (page - 1) * ITEMS_PER_PAGE
    txns = get_transactions(group_id, user_a, user_b, limit=ITEMS_PER_PAGE, offset=offset)

    text = _build_ledger_text(txns, target["username"], page, total_pages)
    keyboard = ledger_pagination_keyboard(page, total_pages, user_a, user_b, group_id)

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


async def settle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not context.args or len(context.args) != 1:
        await msg.reply_text(
            "❓ <b>Usage:</b> /settle @username",
            parse_mode="HTML",
        )
        return

    username = parse_username(context.args[0])
    if not username:
        await msg.reply_text("❌ Please provide a valid @username.")
        return

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id
    price = get_price(group_id)

    target = get_user_by_username(group_id, username)
    if not target:
        await msg.reply_text(f"❌ @{username} is not in the ledger.")
        return

    target_id = target["telegram_user_id"]

    if target_id == caller_id:
        await msg.reply_text("❌ You cannot settle with yourself.")
        return

    net_inr = get_net_balance_inr(group_id, caller_id, target_id)

    if abs(net_inr) < 0.01:
        await msg.reply_text(
            f"⚪ Already settled with @{username}!\n"
            f"Balance is already ₹0.",
        )
        return

    amount_inr  = abs(net_inr)
    amount_usdt = inr_to_usdt(amount_inr, price) if price > 0 else 0

    add_transaction(group_id, caller_id, target_id, net_inr, amount_usdt, "settle", "Settlement")

    await msg.reply_text(
        f"🤝 <b>Ledger Settled!</b>\n\n"
        f"👤 @{target['username']}\n"
        f"💰 Cleared: {format_both(amount_inr, amount_usdt)}\n"
        f"✅ Balance reset to ₹0",
        parse_mode="HTML",
    )
