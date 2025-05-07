# config.py

import os
import json
import base64

# --- Environment Configuration ---
# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing environment variable: BOT_TOKEN")

# Google Service Account JSON stored as Base64 in env var
BASE64_CREDS = os.getenv("BASE64_CREDS")
if not BASE64_CREDS:
    raise RuntimeError("Missing environment variable: BASE64_CREDS")

try:
    creds_json = base64.b64decode(BASE64_CREDS).decode('utf-8')
    SERVICE_ACCOUNT_INFO = json.loads(creds_json)
except Exception as e:
    raise RuntimeError("Invalid BASE64_CREDS: " + str(e))

# The ID of your Google Spreadsheet
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("Missing environment variable: SHEET_ID")

# --- Game Configuration ---
# Maximum levels for each building
BUILDING_MAX_LEVEL = {
    'Mine': 10,
    'Power Plant': 10,
    'Barracks': 10,
    'Workshop': 10,
}

# Unlock requirements for troop tiers
TIER_UNLOCK = {
    2: {'Barracks': 3, 'Workshop': 2},
    3: {'Barracks': 5, 'Workshop': 4},
}

# --- Spoils Configuration ---
# Percentage of each resource stolen on victory
SPOIL_RATE = 0.10  # 10%

# Map resource names to their column index in the Players sheet
RESOURCE_COLUMNS = {
    'credits': 3,
    'minerals': 4,
    'energy': 5,
}
