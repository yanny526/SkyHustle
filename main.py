# utils/main.py
import asyncio
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from handlers import player  # Import the player handlers
from utils.google_sheets import get_sheet  # Import the google_sheets module


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all incoming messages."""

    if not update.message:
        return  # Ignore updates without messages

    sheet = get_sheet()  # Get the sheet object
    if not sheet:
        print("Error: Could not connect to Google Sheets in handle_message")  # Log the error
        return

    cid = update.message.chat_id
    player = get_sheet().find_or_create_player(sheet, cid)  # Use google_sheets module
    # player = find_or_create_player(sheet, cid)
    # ... (Potentially other message handling logic)


async def main():
    """Starts the bot."""

    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("start", player.start_command))
    application.add_handler(CommandHandler("name", player.name_command))
    application.add_handler(CommandHandler("status", player.status_command))

    # Start the Bot
    print("Bot is running...")
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
