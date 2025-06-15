import os
import json

# --- Telegram Bot API Token ---
# Loaded directly from Render environment variable. Must be set.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Google Sheets API Configuration ---
# The *content* of your service account credentials JSON file, loaded directly from an environment variable.
# This variable (GOOGLE_CREDENTIALS_JSON) should contain the entire JSON string. Must be set.
GOOGLE_CREDENTIALS_JSON_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")

# The ID of your Google Spreadsheet where game data will be stored.
# Loaded directly from Render environment variable. Must be set.
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# --- Game Constants ---
# Initial resources for new players
STARTING_RESOURCES = {
    "wood": 500,
    "stone": 500,
    "food": 500,
    "gold": 500,
    "energy": 200,
    "diamonds": 50,
}

# Initial resource caps (Warehouse Level 1 capacity)
INITIAL_RESOURCE_CAPS = {
    "wood": 5000,
    "stone": 5000,
    "food": 5000,
    "gold": 5000,
    "energy": 200,
}

# Initial building levels for new players
INITIAL_BUILDING_LEVELS = {
    "base": 1,
    "lumber_house": 1,
    "mine": 1,
    "warehouse": 1,
    "barracks": 1,
    "power_plant": 1,
    "research_lab": 1,
    "hospital": 0,  # Hospital starts at 0, built later
    "workshop": 0,  # Workshop starts at 0, built later
    "jail": 0,      # Jail starts at 0, built later
}

# Initial empty unit counts for new players
INITIAL_UNIT_COUNTS = {
    "infantry_t1": 0,
    "tanks_t1": 0,
    "artillery_t1": 0,
    "building_destroyers_t1": 0,
    "hazmat_units": 0,
    # Add other tiers (t2, t3) as they are unlocked by Barracks level, initially 0
}

# Game version or other global settings (optional for now)
GAME_VERSION = "0.1.0" 