# content.py
# The central repository for all player-facing text.
# Hotfix applied to correctly display the Food resource line in the base panel.

import constants
from datetime import datetime

def get_welcome_new_player_text():
    """Returns the initial message for a new commander."""
    return (
        "🛰️ **Connection Established.**\n\n"
        "Welcome to SkyHustle, Commander. I am your Central Command AI. "
        "Your command base is being initialized, but it requires your designation.\n\n"
        "What name shall I register for you? ✒️"
    )

def get_new_player_welcome_success_text(commander_name):
    """Returns the welcome message after a new player has successfully chosen a name."""
    return (
        f"Excellent, Commander **{commander_name}**! ✅\n\n"
        "Your identity is confirmed and your journey in SkyHustle begins now. "
        "Your starter pack has been credited to your base.\n\n"
        "Below is your command dashboard. Use the menu to survey your options."
    )

def get_base_panel_text(player_data: dict) -> str:
    """
    Generates the dynamic, HTML-formatted text for the main base panel.
    Now includes total army size.
    """
    # Safely retrieve data using .get() to prevent errors if a key is missing.
    name = player_data.get(constants.FIELD_COMMANDER_NAME, "N/A")
    base_level = player_data.get('base_level', 1)
    power = int(player_data.get('power', 0))
    diamonds = int(player_data.get('diamonds', 0))

    # --- NEW: Calculate total army size ---
    total_units = 0
    for unit_key in constants.UNIT_DATA:
        total_units += int(player_data.get(constants.UNIT_DATA[unit_key]['id'], 0))

    # Resource retrieval
    wood = int(player_data.get('wood', 0))
    stone = int(player_data.get('stone', 0))
    iron = int(player_data.get('iron', 0))
    food = int(player_data.get('food', 0))
    wood_cap = int(player_data.get('wood_storage_cap', 0))
    stone_cap = int(player_data.get('stone_storage_cap', 0))
    iron_cap = int(player_data.get('iron_storage_cap', 0))
    food_cap = int(player_data.get('food_storage_cap', 0))
    wood_prod = int(player_data.get('wood_prod_rate', 0))
    stone_prod = int(player_data.get('stone_prod_rate',0))
    iron_prod = int(player_data.get('iron_prod_rate', 0))
    food_prod = int(player_data.get('food_prod_rate', 0))
    
    # Construct the message with superior formatting and visual cues.
    text = (
        f"<b><u>🏠 Commander {name}'s Base (Lv. {base_level})</u></b>\n\n"
        f"<b>Power:</b> 💪 {power:,}  |  <b>Army:</b> 🪖 {total_units:,}\n"
        f"<b>Diamonds:</b> 💎 {diamonds:,}\n"
        f"────────────────────\n"
        f"<b><u>Resources (Production/hr):</u></b>\n"
        f"🌲 Wood:  {wood:,} / {wood_cap:,} <i>( +{wood_prod:,} )</i>\n"
        f"🪨 Stone: {stone:,} / {stone_cap:,} <i>( +{stone_prod:,} )</i>\n"
        f"🔩 Iron:  {iron:,} / {iron_cap:,} <i>( +{iron_prod:,} )</i>\n"
        f"🍞 Food:  {food:,} / {food_cap:,} <i>( +{food_prod:,} )</i>\n\n"
        f"<i>Status: All systems nominal. ✅</i>"
    )
    return text