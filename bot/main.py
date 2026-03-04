import os
import logging

from dotenv import load_dotenv
from telegram import BotCommand, BotCommandScopeAllGroupChats
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from bot.database.db import init_db
from bot.handlers.price import setprice_cmd, price_cmd
from bot.handlers.convert import convert_cmd
from bot.handlers.users import add_cmd, del_cmd, users_cmd
from bot.handlers.transactions import debit_cmd, credit_cmd, salary_cmd
from bot.handlers.ledger import balance_cmd, ledger_cmd, ledger_callback, settle_cmd
from bot.handlers.export import export_cmd
from bot.handlers.help import help_cmd

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set in .env")

    init_db()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("setprice", setprice_cmd))
    app.add_handler(CommandHandler("price",    price_cmd))
    app.add_handler(CommandHandler("convert",  convert_cmd))
    app.add_handler(CommandHandler("add",      add_cmd))
    app.add_handler(CommandHandler("del",      del_cmd))
    app.add_handler(CommandHandler("users",    users_cmd))
    app.add_handler(CommandHandler("debit",    debit_cmd))
    app.add_handler(CommandHandler("credit",   credit_cmd))
    app.add_handler(CommandHandler("salary",   salary_cmd))
    app.add_handler(CommandHandler("balance",  balance_cmd))
    app.add_handler(CommandHandler("ledger",   ledger_cmd))
    app.add_handler(CommandHandler("settle",   settle_cmd))
    app.add_handler(CommandHandler("export",   export_cmd))
    app.add_handler(CallbackQueryHandler(ledger_callback, pattern=r"^ledger:"))
    app.add_handler(CommandHandler("help",  help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))

    commands = [
        BotCommand("setprice", "Set USDT price in INR (admin)"),
        BotCommand("price",    "Show current USDT rate"),
        BotCommand("convert",  "Convert between INR and USDT"),
        BotCommand("add",      "Add user to ledger (admin)"),
        BotCommand("del",      "Remove user from ledger (admin)"),
        BotCommand("debit",    "Record money you gave to user"),
        BotCommand("credit",   "Record money received from user"),
        BotCommand("salary",   "Record salary paid to user"),
        BotCommand("balance",  "Show balance with a user"),
        BotCommand("ledger",   "Show transaction history with a user"),
        BotCommand("users",    "Show all users with balances"),
        BotCommand("settle",   "Reset balance to zero"),
        BotCommand("export",   "Export ledger to CSV file"),
        BotCommand("help",     "Show command guide"),
    ]
    app.bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())

    logger.info("Bot started in polling mode")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
