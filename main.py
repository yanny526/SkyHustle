# main.py
# System 2 Upgrade: Now initializes the APScheduler engine at startup.

import os
import telebot
import logging
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
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Telegram Bot API initialized.")

# --- NEW: Initialize and start the background scheduler ---
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.start()
logger.info("APScheduler engine started in background.")

# Pass the bot and scheduler instances to the handler registration function
handlers.register_handlers(bot, scheduler)
logger.info("All system handlers have been registered.")

logger.info("SkyHustle is fully operational. Starting bot polling...")
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    logger.critical(f"FATAL ERROR: Bot polling crashed: {e}")