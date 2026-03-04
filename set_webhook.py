"""
Run this once after deploying to PythonAnywhere to register your webhook URL.

Usage:
    python set_webhook.py
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN      = os.getenv("BOT_TOKEN")
WEBHOOK_URL    = os.getenv("WEBHOOK_URL")      # e.g. https://yourname.pythonanywhere.com/webhook
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


async def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set in .env")
        return
    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL not set in .env")
        return

    bot = Bot(token=BOT_TOKEN)

    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )

    info = await bot.get_webhook_info()
    print(f"✅ Webhook set successfully!")
    print(f"   URL    : {info.url}")
    print(f"   Pending: {info.pending_update_count}")
    if info.last_error_message:
        print(f"   ⚠️  Last error: {info.last_error_message}")

    await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
