"""
config.py:

This file stores the configuration settings for the SkyHustle game.
These settings include the Telegram Bot API token, Google Sheets API credentials,
and the ID of the Google Sheet used for data storage.
"""

import os
# Telegram Bot API Token
# Replace with your actual bot token.
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Google Sheets API Credentials (Base64 encoded JSON)
#  Replace with the Base64 encoded content of your Google Sheets API credentials JSON file.
BASE64_CREDS = os.environ["BASE64_CREDS"]
SHEET_ID = os.environ["SHEET_ID"]
# Replace with the ID of your Google Sheet.
# You can find this in the URL of your Google Sheet.
SHEET_ID = "YOUR_SHEET_KEY"  # Example: "1BQiubVRjRTFvD-3j6FZoR97Z_65e99cK4" #Will be read from environment variable

# Game Constants
#  These can be adjusted to change the initial game parameters.
INITIAL_RESOURCES = {
    "sky_iron": 1000,
    "glowstone": 500,
    "circuits": 200,
}

# Fixed travel time for attacks
FIXED_TRAVEL_TIME = 1800  # 30 minutes in seconds

# Resource Production Rates (per hour)
BASE_PRODUCTION_RATES = {
    "iron_harvester": 20,  # Base sky_iron per hour
    "glowstone_refinery": 10,  # Base glowstone per hour
    "circuit_fabricator": 5,  # Base circuits per hour
}

PRODUCTION_BONUS_PER_LEVEL = {
    "iron_harvester": 5,  # Bonus sky_iron per level
    "glowstone_refinery": 3,  # Bonus glowstone per level
    "circuit_fabricator": 2,  # Bonus circuits per level
}

# Building Costs
BUILDING_COSTS = {
    "iron_harvester": {"sky_iron": 100, "glowstone": 50, "circuits": 20},
    "glowstone_refinery": {"sky_iron": 150, "glowstone": 100, "circuits": 30},
    "circuit_fabricator": {"sky_iron": 200, "glowstone": 150, "circuits": 50},
    "shipyard": {"sky_iron": 300, "glowstone": 200, "circuits": 100},
    "defense_platform": {"sky_iron": 250, "glowstone": 150, "circuits": 80},
    "interceptor": {"sky_iron": 50, "glowstone": 20, "circuits": 10},
    "bomber": {"sky_iron": 80, "glowstone": 50, "circuits": 20},
    "destroyer": {"sky_iron": 120, "glowstone": 80, "circuits": 30},
    "cruiser": {"sky_iron": 200, "glowstone": 150, "circuits": 50},
    "carrier": {"sky_iron": 300, "glowstone": 250, "circuits": 100},
    "frigate": {"sky_iron": 100, "glowstone": 75, "circuits": 25},
    "sentinel": {"sky_iron": 400, "glowstone": 300, "circuits": 120},
}
UNIT_TYPES = ["interceptor", "bomber", "destroyer", "cruiser", "carrier", "frigate", "sentinel"]
# Shop Items
SHOP_ITEMS = {
    "unbreakable_shield": {
        "cost": {"sky_iron": 500, "glowstone": 300, "circuits": 200},
        "description": "Grants a ship temporary invulnerability for one battle.",
    },
    "shield_breaker_missile": {
        "cost": {"sky_iron": 400, "glowstone": 400, "circuits": 300},
        "description": "Negates enemy shields for one battle.",
    },
    "spy_probe": {
        "cost": {"sky_iron": 100, "glowstone": 200, "circuits": 100},
        "description": "Gathers intel on a target player's fleet and defenses.",
    },
    "speed_up": {
        "cost": {"sky_iron": 200, "glowstone": 150, "circuits": 100},
        "description": "Reduces the travel time of an attack.",
    }
}
