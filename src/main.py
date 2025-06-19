# src/main.py
import os
import telebot
from dotenv import load_dotenv # Used for local development to load .env file
import logging
import time # Import time for timestamp in ping handler

# Import handlers and other utility modules
from src.bot.handlers import register_handlers
from src.core import constants
from src.utils import google_sheets

# --- Configure Logging ---
# Set up a basic logger for the entire application
logging.basicConfig(
    level=logging.INFO, # Set to INFO to see more details during startup
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Outputs logs to the console/Render logs
        # You can add FileHandler here later for persistent logs:
        # logging.FileHandler("skyhustle.log")
    ]
)
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
# For local development, load from .env file (ensure it's not committed to Git!)
# On Render, environment variables are loaded automatically and securely.
load_dotenv() 

# Retrieve environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
BASE64_CREDS = os.environ.get('BASE64_CREDS')

# Critical checks for essential environment variables
if not BOT_TOKEN:
    logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set. Bot cannot start. Exiting.")
    exit(1)
if not SHEET_ID:
    logger.critical("CRITICAL: SHEET_ID environment variable not set. Bot cannot start. Exiting.")
    exit(1)
if not BASE64_CREDS:
    logger.critical("CRITICAL: BASE64_CREDS environment variable not set. Bot cannot start. Exiting.")
    exit(1)

logger.info("All essential environment variables loaded successfully.")

# --- Initialize Bot ---
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    logger.info("Telegram Bot instance initialized successfully.")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize Telegram Bot with the provided token: {e}. Bot cannot proceed. Exiting.")
    exit(1)

# --- Register Handlers ---
register_handlers(bot)
logger.info("Bot handlers registered.")

# --- Add a simple /ping handler for debugging connectivity ---
@bot.message_handler(commands=['ping'])
def handle_ping(message):
    logger.info(f"Received /ping command from user {message.from_user.id}")
    bot.reply_to(message, f"Pong! Bot is alive. Current UTC time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}")

# --- Verify Google Sheet Connection at Startup ---
try:
    # This call will attempt authentication and ensure the 'Players' worksheet
    # and its headers are correctly set up, or log a critical error and exit if not.
    google_sheets.get_worksheet() 
    logger.info("Successfully connected to and initialized Google Sheet at startup.")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to connect to or initialize Google Sheet at startup: {e}. Bot cannot proceed. Exiting.")
    exit(1)

# --- Start Bot Polling ---
logger.info("Attempting to start bot polling loop...")
try:
    # bot.polling listens for updates from Telegram.
    # none_stop=True keeps it running indefinitely.
    # interval=0 means no delay between checks (for responsiveness).
    # timeout=10 means it will time out if no updates for 10 seconds (useful for detecting hangs).
    bot.polling(none_stop=True, interval=0, timeout=10) 
    logger.info("Bot polling loop started successfully and running.")
except telebot.apihelper.ApiTelegramException as api_e:
    # This specific exception is raised for Telegram API-related issues,
    # often due to an invalid bot token or network problems with Telegram's servers.
    logger.critical(f"CRITICAL: Telegram API Error during polling: {api_e}. "
                     "This often indicates an INVALID BOT_TOKEN or Telegram server issues. Bot stopping.")
    exit(1) # Exit the application if a critical API error occurs
except Exception as e:
    # Catch any other unexpected exceptions that might occur during polling
    logger.critical(f"CRITICAL: An unexpected unhandled error occurred during bot polling: {e}. Bot stopping.")
    exit(1)
