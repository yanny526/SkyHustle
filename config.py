# config.py

# Telegram bot token (keep yours secret!)
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Google Sheets settings
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"

# Maximum levels for each building
BUILDING_MAX_LEVEL = {
    'Mine': 10,
    'Power Plant': 10,
    'Barracks': 10,
    'Workshop': 10,
}

# Unlock requirements for troop tiers
TIER_UNLOCK = {
    2: {'Barracks': 3, 'Workshop': 2},  # Tier 2 requires Barracks ≥ 3, Workshop ≥ 2
    3: {'Barracks': 5, 'Workshop': 4},  # Tier 3 requires Barracks ≥ 5, Workshop ≥ 4
}
