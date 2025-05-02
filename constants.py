# constants.py

"""
This module defines shared constants for the SkyHustle game.
"""

# Command descriptions
START_COMMAND_DESCRIPTION = "/start - Initialize your commander profile"
RESOURCES_COMMAND_DESCRIPTION = "/resources - Show your current resources and production rates"
ATTACK_COMMAND_DESCRIPTION = "/attack <x> <y> - Attack an enemy at coordinates (x, y)"
DEFENSE_COMMAND_DESCRIPTION = "/defense - Display your current defense rating"
SHOP_COMMAND_DESCRIPTION = "/shop - Browse and purchase items from the shop"
HELP_COMMAND_DESCRIPTION = "/help - Display available commands and descriptions"

# Resource, building, and unit types (must match your sheet columns & config)
RESOURCE_NAMES = ["sky_iron", "glowstone", "circuits"]

BUILDING_NAMES = [
    "iron_harvester",
    "glowstone_refinery",
    "circuit_fabricator",
    "shipyard",
    "defense_platform",
]

UNIT_TYPES = [
    "interceptor",
    "bomber",
    "destroyer",
    "cruiser",
    "carrier",
]

# Google Sheet tab names & layout
PLAYER_SHEET_NAME = "Players"
NPC_SHEET_NAME = "NPCs"
NPC_STARTING_ROW = 2
