"""
Configuration module for SkyHustle bot
"""
import os
import json
import base64
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets Configuration
SHEET_ID = os.getenv("SHEET_ID")
BASE64_CREDS = os.getenv("BASE64_CREDS")

# Decode the base64 encoded credentials
def get_google_creds():
    """Decode base64 credentials for Google API"""
    if not BASE64_CREDS:
        raise ValueError("BASE64_CREDS environment variable is not set")
    
    creds_json = base64.b64decode(BASE64_CREDS).decode('utf-8')
    return json.loads(creds_json)

# Game Configuration
RESOURCE_TYPES = ["credits", "minerals", "energy", "skybucks"]
MAX_QUEUE_LENGTH = 5
MAX_NAME_LENGTH = 32
DAILY_REWARDS = {
    "credits": 100,
    "minerals": 50,
    "energy": 50,
}
DAILY_STREAK_BONUS = 0.1  # 10% bonus per consecutive day

# Cache Configuration
CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)

# Rate Limits (to prevent spamming)
RATE_LIMIT = {
    "commands": 20,  # Maximum commands per minute
    "attack": 5,     # Maximum attacks per minute
}

# Sheet Names
SHEET_NAMES = {
    "players": "Players",
    "buildings": "Buildings",
    "units": "Units",
    "research": "Research",
    "alliances": "Alliances",
    "wars": "Wars",
    "battles": "Battles",
    "achievements": "Achievements",
    "events": "Events",
}

# Sheet Column Definitions (for reference)
SHEET_COLUMNS = {
    "players": [
        "player_id", "display_name", "credits", "minerals", "energy", "skybucks",
        "experience", "level", "tutorial_completed", "last_login", "daily_streak",
        "last_daily", "alliance_id"
    ],
    "buildings": [
        "player_id", "building_id", "building_type", "level", "quantity", 
        "build_started", "build_completed"
    ],
    "units": [
        "player_id", "unit_id", "unit_type", "level", "quantity", 
        "train_started", "train_completed"
    ],
    # Add other sheet columns as needed
}
