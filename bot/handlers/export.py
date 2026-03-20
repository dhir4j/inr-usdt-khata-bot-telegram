import csv
import io
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

from telegram import Update
from telegram.ext import ContextTypes

from bot.database.db import get_all_transactions_for_export
from bot.utils.helpers import is_group_chat


async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not is_group_chat(update):
        await msg.reply_text("⚠️ This command works only in groups.")
        return

    group_id = update.effective_chat.id

    await msg.reply_text("⏳ Generating CSV export...")

    rows = get_all_transactions_for_export(group_id)

    if not rows:
        await msg.reply_text("📭 No transactions found to export.")
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["#", "Date", "Type", "From", "Amount (INR)", "Amount (USDT)", "Note"])

    for i, row in enumerate(rows, start=1):
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
            f"{row['amount_inr']:.2f}",
            f"{row['amount_usdt']:.2f}",
            row["note"] or "",
        ])

    output.seek(0)
    csv_bytes = io.BytesIO(output.getvalue().encode("utf-8"))

    chat_title = (update.effective_chat.title or "group").replace(" ", "_")
    date_str  = datetime.now().strftime("%Y%m%d")
    filename  = f"khata_{chat_title}_{date_str}.csv"

    caption = (
        f"📊 <b>Ledger Export</b>\n\n"
        f"🔢 Rows: {len(rows)}\n"
        f"📅 Exported: {datetime.now().strftime('%d %b %Y %H:%M')}"
    )

    await msg.reply_document(
        document=csv_bytes,
        filename=filename,
        caption=caption,
        parse_mode="HTML",
    )
