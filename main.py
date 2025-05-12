"""
Main entry point for the SkyHustle Telegram bot application.
This script initializes the Telegram bot and registers all command handlers.
"""
import os
import logging
from app import app  # Flask app for web dashboard

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Only run the bot when executed directly (not imported by gunicorn)
if __name__ == "__main__":
    try:
        # Import the bot handlers
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, Dispatcher
        from handlers.base_handlers import (
            start, status, help_command, setname, daily, weather, events, 
            achievements, save, load, leaderboard, notifications, callback_handler
        )
        from handlers.building_handlers import build, defensive
        from handlers.alliance_handlers import alliance, war
        from handlers.combat_handlers import attack, scan, unit_evolution
        from handlers.tutorial_handlers import tutorial

        # Initialize the Telegram bot
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN environment variable not found!")
            exit(1)
            
        # Create and configure the bot
        updater = Updater(token=bot_token, use_context=True)
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
        updater.idle()
    except ImportError as e:
        logger.error(f"Import error when starting bot: {e}")
    except Exception as e:
        logger.error(f"General error when starting bot: {e}")
