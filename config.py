# config.py
import os
import json

# Telegram bot token (set as an environment variable in your deploy)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets credentials: store the JSON in an env var "SERVICE_ACCOUNT_INFO"
# and your Sheet ID in "SHEET_ID"
SERVICE_ACCOUNT_INFO = json.loads(os.getenv("SERVICE_ACCOUNT_INFO"))
SHEET_ID = os.getenv("SHEET_ID")

# --- Game Settings ---
# Maximum levels for each building
BUILDING_MAX_LEVEL = {
    'Mine': 10,
    'Power Plant': 10,
    'Barracks': 10,
    'Workshop': 10,
}

# Unlock requirements for troop tiers
# Tier 2 unlocks at Barracks>=3 and Workshop>=2
# Tier 3 unlocks at Barracks>=5 and Workshop>=4
TIER_UNLOCK = {
    2: {'Barracks': 3, 'Workshop': 2},
    3: {'Barracks': 5, 'Workshop': 4},
}
