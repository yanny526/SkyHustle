 # content.py
# The central repository for all player-facing text.
# This separation of content from logic is a hallmark of superior engineering.

import constants
from datetime import datetime

def get_welcome_new_player_text():
    """Returns the initial message for a new commander."""
    return (
        "🛰️ **Connection Established.**\n\n"
        "Welcome, Commander. I am the Central Command Unit for SkyHustle. "
        "Your command base is being initialized, but it requires your designation.\n\n"
        "What shall I call you?"
    )

def get_new_player_welcome_success_text(commander_name):
    """Returns the welcome message after a new player has successfully chosen a name."""
    return (
        f"Excellent, Commander **{commander_name}**!\n\n"
        "Your identity is confirmed. Your journey in SkyHustle begins now. "
        "Your starter pack has been credited to your account.\n\n"
        "Use the menu below to survey your base."
    )

def get_base_panel_text(player_data: dict) -> str:
    """
    Generates the dynamic, HTML-formatted text for the main /base panel.
    This function is engineered to be robust, safely handling potentially missing data.
    """
    # Safely retrieve data using .get() to prevent errors if a key is missing.
    name = player_data.get(constants.FIELD_COMMANDER_NAME, "N/A")
    base_level = player_data.get('base_level', 1)
    power = player_data.get('power', 0)
    wood = int(player_data.get('wood', 0))
    stone = int(player_data.get('stone', 0))
    iron = int(player_data.get('iron', 0))
    wood_cap = int(player_data.get('wood_storage_cap', 0))
    stone_cap = int(player_data.get('stone_storage_cap', 0))
    iron_cap = int(player_data.get('iron_storage_cap', 0))
    wood_prod = int(player_data.get('wood_prod_rate', 0))
    stone_prod = int(player_data.get('stone_prod_rate',0))
    iron_prod = int(player_data.get('iron_prod_rate', 0))
    
    # Construct the message with precision.
    text = (
        f"<b><u>🏠 Commander {name}'s Base (Lv. {base_level})</u></b>\n"
        f"<b>Power:</b> 💪 {power}\n\n"
        f"<b><u>Resources (Production/hr):</u></b>\n"
        f"    🌲 Wood:  {wood:,}/{wood_cap:,} <i>( +{wood_prod:,} )</i>\n"
        f"    🪨 Stone: {stone:,}/{stone_cap:,} <i>( +{stone_prod:,} )</i>\n"
        f"    🔩 Iron:  {iron:,}/{iron_cap:,} <i>( +{iron_prod:,} )</i>\n\n"
        f"<i>Select an option from the menu to proceed.</i>"
    )
    return text