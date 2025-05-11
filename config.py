"""
Configuration settings for the SkyHustle application.
Loads environment variables and provides configuration constants.
"""
import os
import base64
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (for development)
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.warning("BOT_TOKEN environment variable not found!")

# Google Sheets configuration
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    logging.warning("SHEET_ID environment variable not found!")

# Base64-encoded Google service account credentials
BASE64_CREDS = os.getenv("BASE64_CREDS")
if BASE64_CREDS:
    try:
        # Decode base64 credentials to JSON
        GOOGLE_CREDS_JSON = json.loads(base64.b64decode(BASE64_CREDS).decode('utf-8'))
    except Exception as e:
        logging.error(f"Failed to decode BASE64_CREDS: {e}")
        GOOGLE_CREDS_JSON = None
else:
    logging.warning("BASE64_CREDS environment variable not found!")
    GOOGLE_CREDS_JSON = None

# Game configuration constants
STARTING_RESOURCES = {
    "credits": 1000,
    "minerals": 500,
    "energy": 500,
    "skybucks": 0  # Premium currency
}

# Sheet names in Google Sheets
SHEET_NAMES = {
    "players": "Players",
    "buildings": "Buildings",
    "units": "Units",
    "research": "Research",
    "alliances": "Alliances",
    "wars": "Wars",
    "events": "Events"
}

# Game mechanics constants
MAX_BUILD_QUEUE_LENGTH = 5
MAX_ALLIANCE_SIZE = 20
MAX_NAME_LENGTH = 32
DAILY_REWARD = {
    "credits": 100,
    "minerals": 50,
    "energy": 50
}

# Command retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
