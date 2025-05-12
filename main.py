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
    from telegram import Bot, Update
    from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, Dispatcher
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
    
    # Create the Updater and pass it the bot's token
    updater = Updater(token=bot_token, use_context=True)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("build", build))
    dispatcher.add_handler(CommandHandler("train", lambda update, context: 
                                          update.message.reply_text("Not implemented yet")))
    dispatcher.add_handler(CommandHandler("research", lambda update, context: 
                                          update.message.reply_text("Not implemented yet")))
    dispatcher.add_handler(CommandHandler("unit_evolution", unit_evolution))
    dispatcher.add_handler(CommandHandler("defensive", defensive))
    dispatcher.add_handler(CommandHandler("attack", attack))
    dispatcher.add_handler(CommandHandler("scan", scan))
    dispatcher.add_handler(CommandHandler("alliance", alliance))
    dispatcher.add_handler(CommandHandler("war", war))
    dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))
    dispatcher.add_handler(CommandHandler("daily", daily))
    dispatcher.add_handler(CommandHandler("achievements", achievements))
    dispatcher.add_handler(CommandHandler("events", events))
    dispatcher.add_handler(CommandHandler("notifications", notifications))
    dispatcher.add_handler(CommandHandler("tutorial", tutorial))
    dispatcher.add_handler(CommandHandler("weather", weather))
    dispatcher.add_handler(CommandHandler("save", save))
    dispatcher.add_handler(CommandHandler("load", load))
    dispatcher.add_handler(CommandHandler("setname", setname))
    
    # Register callback query handler for inline keyboard buttons
    dispatcher.add_handler(CallbackQueryHandler(callback_handler))
    
    # Start the Bot
    logger.info("Starting SkyHustle bot...")
    updater.start_polling()
    
    # Run the bot until the process is stopped
    updater.idle()

# Start Flask app in a separate thread if needed
# import threading
# def run_flask():
#     app.run(host='0.0.0.0', port=5000, debug=True)
# flask_thread = threading.Thread(target=run_flask)
# flask_thread.start()
