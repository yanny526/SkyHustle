# main.py
import os
import sys
import signal
from dotenv import load_dotenv
from telegram.ext import Application, JobQueue, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.error import Conflict
from modules.sheets_helper import initialize_sheets
from modules.registration import setup_registration, ENTER_BASE
from modules.base_ui import setup_base_ui, tick_resources, base_handler
from modules.building_system import (
    build_menu, build_choice, confirm_build, cancel_build,
    show_building_info, start_upgrade_worker, view_queue, setup_building_system
)
from modules.troop_system import setup_troop_system
from modules.training_system import setup_training_system
from modules.research_system import setup_research_system
from modules.black_market import setup_black_market
from modules.inventory_system import setup_inventory_system
from modules.alliance_system import setup_alliance_system
from modules.zone_system import setup_zone_system
from telegram import Update
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutting down bot gracefully...")
    sys.exit(0)

def main() -> None:
    logger.info("Bot main function starting...")
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load environment variables from .env if it exists (for local development)
    if os.path.exists('.env'):
        load_dotenv()
    
    # Log environment variable status (without exposing values)
    logger.info("Checking environment variables...")
    required_vars = ["BOT_TOKEN", "BASE64_CREDS", "SHEET_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    logger.info("All required environment variables are present")
    
    # Initialize Google Sheets
    try:
        initialize_sheets()
        logger.info("Successfully initialized Google Sheets connection")
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets: {e}")
        sys.exit(1)
    
    # Build the application
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Register handlers
    setup_registration(app)
    setup_base_ui(app)
    # Building system handlers
    app.add_handler(CommandHandler("build", build_menu))
    app.add_handler(CallbackQueryHandler(build_menu, pattern="^BUILD_MENU$"))
    app.add_handler(CallbackQueryHandler(build_choice, pattern="^BUILD_[a-z_]+$"))
    app.add_handler(CallbackQueryHandler(confirm_build, pattern="^CONFIRM_[a-z_]+$"))
    app.add_handler(CallbackQueryHandler(cancel_build, pattern="^CANCEL_BUILD$"))
    app.add_handler(CallbackQueryHandler(show_building_info, pattern="^INFO_[a-z_]+$"))
    app.add_handler(CallbackQueryHandler(view_queue, pattern="^view_queue$"))
    setup_training_system(app)
    setup_research_system(app)
    setup_black_market(app)
    setup_inventory_system(app)
    setup_alliance_system(app)
    setup_zone_system(app)
    setup_building_system(app)
    setup_troop_system(app)

    # Register the 'Enter Your Base' callback separately to ensure it always works
    app.add_handler(CallbackQueryHandler(base_handler, pattern=f"^{ENTER_BASE}$", block=False))

    # Temporary test command for debugging
    async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info("--- /test command received ---")
        await update.message.reply_text("Test command received successfully!")
    app.add_handler(CommandHandler("test", test_command))

    # schedule resource ticks every minute:
    job_queue = app.job_queue
    job_queue.run_repeating(
        tick_resources,
        interval=60,           # seconds
        first=0,               # run immediately on startup
        name="resource_tick"
    )
    
    # Start the upgrade worker
    job_queue.run_once(start_upgrade_worker, when=0)
    
    # Start the bot with error handling
    try:
        app.run_polling()
    except Conflict as e:
        logger.error("Error: Another instance of the bot is already running.")
        logger.error("Please make sure only one instance is running at a time.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 