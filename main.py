# main.py
# Final Production-Ready Version: Includes a self-healing, resilient polling loop.

import os
import telebot
import logging
import time # <-- NEW: Import the time module for sleep functionality
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

import handlers
import google_sheets

# --- 1. Master Configuration & Initialization ---
# This section is stable and unchanged.
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=======================================")
logger.info("  INITIALIZING SKYHUSTLE COMMAND CORE  ")
logger.info("=======================================")


# --- 2. Critical Pre-Flight Checks ---
# This section is stable and unchanged.
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
BASE64_CREDS = os.environ.get('BASE64_CREDS')

if not all([BOT_TOKEN, SHEET_ID, BASE64_CREDS]):
    logger.critical("FATAL ERROR: Missing critical environment variables.")
    exit(1)

try:
    logger.info("Performing Google Sheets connection health check...")
    google_sheets.get_worksheet()
    logger.info("Google Sheets connection VERIFIED.")
except Exception as e:
    logger.critical(f"FATAL ERROR: Could not connect to Google Sheets at startup: {e}")
    exit(1)


# --- 3. System Assembly & Launch ---
# This section is stable and unchanged.
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Telegram Bot API initialized.")

scheduler = BackgroundScheduler(timezone="UTC")
scheduler.start()
logger.info("APScheduler engine started in background.")

handlers.register_handlers(bot, scheduler)
logger.info("All system handlers have been registered.")


# --- 4. LAUNCH SEQUENCE (with Self-Healing Loop) ---
# This is the upgraded, resilient launch mechanism.
logger.info("SkyHustle is fully operational. Starting resilient bot polling...")

while True:
    try:
        # Start the bot's polling loop. This listens for messages.
        # The timeout parameter helps in handling network issues gracefully.
        bot.polling(none_stop=True, interval=0, timeout=40)
        
    except Exception as e:
        # If any exception occurs (including network errors), log it.
        logger.error(f"CRITICAL: Bot polling loop crashed with error: {e}")
        logger.info("Network anomaly detected. Attempting to restart in 15 seconds...")
        
        # Wait for 15 seconds before restarting the loop.
        # This prevents spamming connection requests during a major outage.
        time.sleep(15)