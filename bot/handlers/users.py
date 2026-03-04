from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import (
    add_user, remove_user, get_user_by_username, get_all_users,
    get_net_balance_inr, get_price,
)
from bot.services.converter import inr_to_usdt
from bot.utils.helpers import is_group_admin, is_group_chat, parse_username, format_both


async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not await is_group_admin(update):
        await msg.reply_text("🚫 Only group admins can add users.")
        return

    if not context.args or len(context.args) != 1:
        await msg.reply_text(
            "❓ <b>Usage:</b> /add @username",
            parse_mode="HTML",
        )
        return

    username = parse_username(context.args[0])
    if not username:
        await msg.reply_text("❌ Please provide a valid @username.")
        return

    group_id = update.effective_chat.id

    telegram_user_id = None
    first_name = username
    if msg.entities:
        for entity in msg.entities:
            if entity.type == "text_mention" and entity.user:
                telegram_user_id = entity.user.id
                first_name = entity.user.first_name or username
                break

    if telegram_user_id is None:
        telegram_user_id = 0

    success = add_user(group_id, telegram_user_id, username, first_name)

    if not success:
        await msg.reply_text(
            f"⚠️ @{username} is already in the ledger.",
            parse_mode="HTML",
        )
        return

    await msg.reply_text(
        f"✅ <b>User Added to Ledger</b>\n\n"
        f"👤 @{username}\n"
        f"💰 Initial Balance: ₹0",
        parse_mode="HTML",
    )


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    if not await is_group_admin(update):
        await msg.reply_text("🚫 Only group admins can remove users.")
        return

    if not context.args or len(context.args) != 1:
        await msg.reply_text(
            "❓ <b>Usage:</b> /del @username",
            parse_mode="HTML",
        )
        return

    username = parse_username(context.args[0])
    if not username:
        await msg.reply_text("❌ Please provide a valid @username.")
        return

    group_id = update.effective_chat.id
    target = get_user_by_username(group_id, username)

    if not target:
        await msg.reply_text(f"❌ @{username} is not in the ledger.")
        return

    all_users = get_all_users(group_id)

    for u in all_users:
        if u["telegram_user_id"] == target["telegram_user_id"]:
            continue
        net = get_net_balance_inr(group_id, u["telegram_user_id"], target["telegram_user_id"])
        if abs(net) > 0.01:
            await msg.reply_text(
                f"🚫 <b>Cannot Remove User</b>\n\n"
                f"👤 @{username} has a pending balance of\n"
                f"💰 ₹{abs(net):,.2f}\n\n"
                f"Settle all dues first with /settle",
                parse_mode="HTML",
            )
            return

    remove_user(group_id, target["telegram_user_id"])
    await msg.reply_text(
        f"🗑️ <b>User Removed</b>\n\n"
        f"👤 @{username} has been removed from the ledger.",
        parse_mode="HTML",
    )


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id
    all_users = get_all_users(group_id)
    price = get_price(group_id)

    if not all_users:
        await msg.reply_text(
            "📭 No users in the ledger yet.\n"
            "👉 Use /add @username to add users.",
        )
        return

    lines = ["📋 <b>Group Ledger Summary</b>\n━━━━━━━━━━━━━━\n"]
    has_others = False

    for u in all_users:
        uid = u["telegram_user_id"]
        uname = u["username"]

        if uid == caller_id:
            continue

        has_others = True
        net = get_net_balance_inr(group_id, caller_id, uid)
        usdt_val = inr_to_usdt(abs(net), price) if price > 0 else 0

        if net > 0.01:
            lines.append(f"🟢 @{uname}\n    +₹{net:,.2f} ({usdt_val:,.2f} USDT)")
        elif net < -0.01:
            lines.append(f"🔴 @{uname}\n    -₹{abs(net):,.2f} ({usdt_val:,.2f} USDT)")
        else:
            lines.append(f"⚪ @{uname}  —  Settled")

    if not has_others:
        lines.append("No other users to show.")

    lines.append(
        "\n━━━━━━━━━━━━━━\n"
        "🟢 They owe you\n"
        "🔴 You owe them\n"
        "⚪ Settled"
    )

    await msg.reply_text("\n".join(lines), parse_mode="HTML")
