import csv
import io
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import get_user_by_username, get_all_transactions_for_export
from bot.utils.helpers import is_group_chat, parse_username


async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    group_id = update.effective_chat.id
    caller_id = update.effective_user.id

    # /export          → all group transactions
    # /export @user    → between caller and that user
    target = None
    if context.args:
        username = parse_username(context.args[0])
        if not username:
            await msg.reply_text("❌ Please provide a valid @username.")
            return
        target = get_user_by_username(group_id, username)
        if not target:
            await msg.reply_text(f"❌ @{username} is not in the ledger.")
            return

    await msg.reply_text("⏳ Generating CSV export...")

    if target:
        rows = get_all_transactions_for_export(group_id, caller_id, target["telegram_user_id"])
        filename_tag = f"with_{target['username']}"
    else:
        rows = get_all_transactions_for_export(group_id)
        chat_title = (update.effective_chat.title or "group").replace(" ", "_")
        filename_tag = chat_title

    if not rows:
        await msg.reply_text("📭 No transactions found to export.")
        return

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["#", "Date", "Type", "From", "To", "Amount (INR)", "Amount (USDT)", "Note"])

    for i, row in enumerate(rows, start=1):
        # Convert stored UTC timestamp to IST
        raw = row["created_at"][:19].replace("T", " ")
        try:
            utc_dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            ist_dt = utc_dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            ist_dt = raw

        writer.writerow([
            i,
            ist_dt,
            row["type"].title(),
            f"@{row['from_username']}" if row["from_username"] else "unknown",
            f"@{row['to_username']}"   if row["to_username"]   else "unknown",
            f"{row['amount_inr']:.2f}",
            f"{row['amount_usdt']:.2f}",
            row["note"] or "",
        ])

    output.seek(0)
    csv_bytes = io.BytesIO(output.getvalue().encode("utf-8"))

    date_str  = datetime.now().strftime("%Y%m%d")
    filename  = f"khata_{filename_tag}_{date_str}.csv"

    scope = f"@{target['username']}" if target else "all transactions"
    caption = (
        f"📊 <b>Ledger Export</b>\n\n"
        f"📁 Scope: {scope}\n"
        f"🔢 Rows: {len(rows)}\n"
        f"📅 Exported: {datetime.now().strftime('%d %b %Y %H:%M')}"
    )

    await msg.reply_document(
        document=csv_bytes,
        filename=filename,
        caption=caption,
        parse_mode="HTML",
    )
