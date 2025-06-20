# main.py
# Definitive Version: Performs a health check on both Players and Alliances worksheets.

import os
import telebot
import logging
import time
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

import handlers
import google_sheets

# --- 1. Master Configuration & Initialization ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=======================================")
logger.info("  INITIALIZING SKYHUSTLE COMMAND CORE  ")
logger.info("=======================================")


# --- 2. Critical Pre-Flight Checks ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.critical("FATAL ERROR: BOT_TOKEN is missing.")
    exit(1)

try:
    logger.info("Performing comprehensive Google Sheets connection health check...")
    # This block now calls the new, specific functions.
    google_sheets.get_players_worksheet()
    google_sheets.get_alliances_worksheet()
    logger.info("All Google Sheets connections VERIFIED.")
except Exception as e:
    logger.critical(f"FATAL ERROR: Could not establish connection with Google Sheets at startup. Halting. Error: {e}")
    exit(1)

# --- 3. System Assembly & Launch ---
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Telegram Bot API initialized.")

scheduler = BackgroundScheduler(timezone="UTC")
scheduler.start()
logger.info("APScheduler engine started in background.")

handlers.register_handlers(bot, scheduler)
logger.info("All system handlers have been registered.")


# --- 4. LAUNCH SEQUENCE (Resilient Loop) ---
logger.info("SkyHustle is fully operational. Starting resilient bot polling...")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=40)
    except Exception as e:
        logger.error(f"CRITICAL: Bot polling loop crashed with error: {e}")
        logger.info("Network anomaly detected. Attempting to restart in 15 seconds...")
        time.sleep(15)