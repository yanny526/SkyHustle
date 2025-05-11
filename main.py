"""
Main entry point for the SkyHustle Telegram bot application.
This script initializes the Telegram bot and registers all command handlers.
"""
import os
import logging
import asyncio
from app import app  # Flask app for web dashboard

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Only run the bot when executed directly (not imported)
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
    from handlers.base_handlers import (
        start, status, help_command, setname, daily, weather, events, 
        achievements, save, load, leaderboard, notifications, callback_handler
    )
    from handlers.building_handlers import build, defensive
    from handlers.alliance_handlers import alliance, war
    from handlers.combat_handlers import attack, scan, unit_evolution
    from handlers.tutorial_handlers import tutorial
    
    # Initialize the bot with token from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not found!")
        exit(1)
    
    application = ApplicationBuilder().token(bot_token).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("build", build))
    application.add_handler(CommandHandler("train", lambda update, context: 
                                          update.message.reply_text("Not implemented yet")))
    application.add_handler(CommandHandler("research", lambda update, context: 
                                          update.message.reply_text("Not implemented yet")))
    application.add_handler(CommandHandler("unit_evolution", unit_evolution))
    application.add_handler(CommandHandler("defensive", defensive))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("alliance", alliance))
    application.add_handler(CommandHandler("war", war))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("achievements", achievements))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CommandHandler("notifications", notifications))
    application.add_handler(CommandHandler("tutorial", tutorial))
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("save", save))
    application.add_handler(CommandHandler("load", load))
    application.add_handler(CommandHandler("setname", setname))
    
    # Register callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Start the Bot
    logger.info("Starting SkyHustle bot...")
    application.run_polling()

# Start Flask app in a separate thread if needed
# import threading
# def run_flask():
#     app.run(host='0.0.0.0', port=5000, debug=True)
# flask_thread = threading.Thread(target=run_flask)
# flask_thread.start()
