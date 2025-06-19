 # main.py
# The central execution core for SkyHustle.
# This file initializes all systems, performs critical startup checks, and launches the bot.
# Its design is clean, delegating logic to specialized modules.

import os
import telebot
import logging
from dotenv import load_dotenv

# Import our custom-engineered modules
import handlers
import google_sheets

# --- 1. Master Configuration & Initialization ---
# Load environment variables from .env for local development.
# On a server like Render, these are set directly in the environment.
load_dotenv()

# Set up a high-quality, informative logger.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

logger.info("=======================================")
logger.info("  INITIALIZING SKYHUSTLE COMMAND CORE  ")
logger.info("=======================================")

# --- 2. Critical Pre-Flight Checks ---
# A superior system verifies its dependencies before launch.
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
BASE64_CREDS = os.environ.get('BASE64_CREDS')

if not all([BOT_TOKEN, SHEET_ID, BASE64_CREDS]):
    logger.critical("FATAL ERROR: One or more environment variables (BOT_TOKEN, SHEET_ID, BASE64_CREDS) are missing.")
    exit(1) # Halt execution if configuration is incomplete.

try:
    logger.info("Performing Google Sheets connection health check...")
    google_sheets.get_worksheet()
    logger.info("Google Sheets connection VERIFIED.")
except Exception as e:
    logger.critical(f"FATAL ERROR: Could not establish connection with Google Sheets at startup. Halting. Error: {e}")
    exit(1)

# --- 3. System Assembly & Launch ---
# Initialize the bot with the provided token.
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Telegram Bot API initialized.")

# Register all command and message handlers from our dedicated logic module.
handlers.register_handlers(bot)
logger.info("All system handlers have been registered.")

logger.info("SkyHustle is fully operational. Starting bot polling...")
try:
    # Launch the bot. It will now listen for commands indefinitely.
    # none_stop=True ensures it runs continuously, even after minor errors.
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    logger.critical(f"FATAL ERROR: Bot polling crashed with an unrecoverable error: {e}")