#!/usr/bin/env python3
"""
Simple test script for Telegram bot
"""
import os
import asyncio
import logging
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    logging.info(f"Received /start command from user: {update.effective_user.id}")
    await update.message.reply_text('Hello! This is a test bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    logging.info(f"Received /help command from user: {update.effective_user.id}")
    await update.message.reply_text('This is a test bot. Available commands: /start, /help, /ping')

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /ping command"""
    logging.info(f"Received /ping command from user: {update.effective_user.id}")
    await update.message.reply_text('Pong!')

async def main() -> None:
    """Run the test bot"""
    # Get the bot token from environment variables
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logging.error("BOT_TOKEN environment variable not set")
        return

    # Create the application
    application = ApplicationBuilder().token(bot_token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))

    # Delete any existing webhook
    logging.info("Deleting existing webhooks...")
    await application.bot.delete_webhook(drop_pending_updates=True)

    # Log bot info
    bot_info = await application.bot.get_me()
    logging.info(f"Starting test bot: {bot_info.first_name} (@{bot_info.username})")

    # Start polling
    logging.info("Starting polling...")
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Keep the application running
    try:
        logging.info("Bot is running...")
        while True:
            await asyncio.sleep(60)
            logging.info("Bot is still running...")
    except (KeyboardInterrupt, SystemExit):
        logging.info("Stopping bot...")
    finally:
        await application.stop()

if __name__ == '__main__':
    asyncio.run(main())