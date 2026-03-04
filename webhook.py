"""
PythonAnywhere webhook entry point.

Point your PythonAnywhere WSGI config to this file:
    from webhook import flask_app as application
"""

import os
import asyncio
import logging

from dotenv import load_dotenv
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from bot.database.db import init_db
from bot.handlers.price import setprice_cmd, price_cmd
from bot.handlers.convert import convert_cmd
from bot.handlers.users import add_cmd, del_cmd, users_cmd
from bot.handlers.transactions import debit_cmd, credit_cmd, salary_cmd
from bot.handlers.ledger import balance_cmd, ledger_cmd, ledger_callback, settle_cmd
from bot.handlers.help import help_cmd
from bot.main import register_commands

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Build PTB application ────────────────────────────────────────────────────

BOT_TOKEN     = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")   # optional but recommended

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

init_db()

ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Register all handlers (same as polling mode)
ptb_app.add_handler(CommandHandler("setprice", setprice_cmd))
ptb_app.add_handler(CommandHandler("price",    price_cmd))
ptb_app.add_handler(CommandHandler("convert",  convert_cmd))
ptb_app.add_handler(CommandHandler("add",      add_cmd))
ptb_app.add_handler(CommandHandler("del",      del_cmd))
ptb_app.add_handler(CommandHandler("users",    users_cmd))
ptb_app.add_handler(CommandHandler("debit",    debit_cmd))
ptb_app.add_handler(CommandHandler("credit",   credit_cmd))
ptb_app.add_handler(CommandHandler("salary",   salary_cmd))
ptb_app.add_handler(CommandHandler("balance",  balance_cmd))
ptb_app.add_handler(CommandHandler("ledger",   ledger_cmd))
ptb_app.add_handler(CommandHandler("settle",   settle_cmd))
ptb_app.add_handler(CallbackQueryHandler(ledger_callback, pattern=r"^ledger:"))
ptb_app.add_handler(CommandHandler("help",  help_cmd))
ptb_app.add_handler(CommandHandler("start", help_cmd))

# ── Shared event loop (reused across requests) ───────────────────────────────

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


def _run(coro):
    return _loop.run_until_complete(coro)


# Initialize the PTB application once at startup
_run(ptb_app.initialize())
logger.info("PTB application initialised")

# Register bot commands (/ menu in Telegram)
_run(register_commands(ptb_app.bot))
logger.info("Bot commands registered")

# ── Flask app ────────────────────────────────────────────────────────────────

flask_app = Flask(__name__)


@flask_app.route("/webhook", methods=["POST"])
def webhook():
    # Validate secret token header if configured
    if WEBHOOK_SECRET:
        token_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token_header != WEBHOOK_SECRET:
            logger.warning("Webhook received with invalid secret token")
            abort(403)

    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400)

    update = Update.de_json(data, ptb_app.bot)
    _run(ptb_app.process_update(update))
    return "OK", 200


@flask_app.route("/", methods=["GET"])
def index():
    return "Khata Bot is running ✅", 200


# ── PythonAnywhere WSGI export ───────────────────────────────────────────────
# PythonAnywhere WSGI file should contain:
#   from webhook import flask_app as application
application = flask_app
