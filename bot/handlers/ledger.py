import math

from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import (
    get_price, get_balance, get_net_balance_inr,
    get_transactions, count_transactions,
    add_transaction, GROUP_SENTINEL,
)
from bot.services.converter import inr_to_usdt
from bot.utils.helpers import is_group_chat, format_both
from bot.keyboards.pagination import ledger_pagination_keyboard

ITEMS_PER_PAGE = 10

TXN_ICONS = {
    "debit":  "📤",
    "credit": "📥",
    "settle": "🤝",
}


def _build_ledger_text(transactions, page: int, total_pages: int) -> str:
    lines = [
        "📒 <b>Your Group Ledger</b>",
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

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id
    price = get_price(group_id)

    bal = get_balance(group_id, caller_id, GROUP_SENTINEL)
    gave_inr     = bal["gave_inr"]
    received_inr = bal["received_inr"]
    net_inr      = bal["net_inr"]

    gave_usdt     = inr_to_usdt(gave_inr, price)     if price > 0 else 0
    received_usdt = inr_to_usdt(received_inr, price) if price > 0 else 0
    net_usdt      = inr_to_usdt(abs(net_inr), price) if price > 0 else 0

    if net_inr > 0.01:
        status_line = f"✅ <b>Group owes you</b>\n💰 {format_both(net_inr, net_usdt)}"
    elif net_inr < -0.01:
        status_line = f"🔴 <b>You owe group</b>\n💰 {format_both(abs(net_inr), net_usdt)}"
    else:
        status_line = "⚪ <b>All settled!</b>  Balance = ₹0"

    text = (
        f"📊 <b>Your Balance with Group</b>\n"
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

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id

    total = count_transactions(group_id, caller_id, GROUP_SENTINEL)
    if total == 0:
        await msg.reply_text("📭 No transactions found for you in this group.")
        return

    total_pages = math.ceil(total / ITEMS_PER_PAGE)
    txns = get_transactions(group_id, caller_id, GROUP_SENTINEL, limit=ITEMS_PER_PAGE, offset=0)

    text = _build_ledger_text(txns, 1, total_pages)
    keyboard = ledger_pagination_keyboard(1, total_pages, caller_id, GROUP_SENTINEL, group_id)

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

    total = count_transactions(group_id, user_a, user_b)
    total_pages = math.ceil(total / ITEMS_PER_PAGE)

    if page < 1 or page > total_pages:
        return

    offset = (page - 1) * ITEMS_PER_PAGE
    txns = get_transactions(group_id, user_a, user_b, limit=ITEMS_PER_PAGE, offset=offset)

    text = _build_ledger_text(txns, page, total_pages)
    keyboard = ledger_pagination_keyboard(page, total_pages, user_a, user_b, group_id)

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


async def settle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id
    price = get_price(group_id)

    net_inr = get_net_balance_inr(group_id, caller_id, GROUP_SENTINEL)

    if abs(net_inr) < 0.01:
        await msg.reply_text("⚪ Already settled!\nYour balance with the group is ₹0.")
        return

    amount_inr  = abs(net_inr)
    amount_usdt = inr_to_usdt(amount_inr, price) if price > 0 else 0

    add_transaction(group_id, caller_id, GROUP_SENTINEL, net_inr, amount_usdt, "settle", "Settlement")

    await msg.reply_text(
        f"🤝 <b>Settled!</b>\n\n"
        f"💰 Cleared: {format_both(amount_inr, amount_usdt)}\n"
        f"✅ Your balance with group reset to ₹0",
        parse_mode="HTML",
    )
