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
    decoded = base64.b64decode(BASE64_CREDS)
    SERVICE_ACCOUNT_INFO = json.loads(decoded)
except Exception as e:
    raise RuntimeError("Invalid BASE64_CREDS: must be base64‑encoded JSON string") from e

# Google Sheets ID
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("Missing environment variable: SHEET_ID")

# --- Game Settings ---
# Maximum levels for each building
BUILDING_MAX_LEVEL = {
    'Mine': 10,
    'Power Plant': 10,
    'Barracks': 10,
    'Workshop': 10,
}

# Unlock requirements for troop tiers
tier_unlock = {
    2: {'Barracks': 3, 'Workshop': 2},
    3: {'Barracks': 5, 'Workshop': 4},
}
# Make dict available for imports
TIER_UNLOCK = tier_unlock
