import logging
import os

from telegram.ext import ApplicationBuilder, CommandHandler

# load your bot token
from config import BOT_TOKEN

# initialize your Google Sheets client
from sheets_service import init as sheets_init

# import command handlers
from handlers.start       import handler as start_handler
from handlers.help        import handler as help_handler
from handlers.status      import handler as status_handler
from handlers.army        import handler as army_handler
from handlers.upgrade     import handler as upgrade_handler
from handlers.train       import handler as train_handler
from handlers.leaderboard import handler as leaderboard_handler

async def unknown_command(update, context):
    await update.message.reply_text(
        "🤔 I don't recognize that command. Type /help to see what's available."
    )

def main():
    # basic logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # init Sheets (must happen before any handler that uses it)
    sheets_init()

    # build the bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # register the handlers
    app.add_handler(CommandHandler("start",       start_handler))
    app.add_handler(CommandHandler("help",        help_handler))
    app.add_handler(CommandHandler("status",      status_handler))
    app.add_handler(CommandHandler("army",        army_handler))
    app.add_handler(CommandHandler("upgrade",     upgrade_handler))
    app.add_handler(CommandHandler("train",       train_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))

    # catch-all for unknown commands
    app.add_handler(CommandHandler(None, unknown_command))

    # run until Ctrl‑C
    app.run_polling()

if __name__ == "__main__":
    main()
