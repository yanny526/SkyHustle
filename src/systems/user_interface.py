# src/systems/user_interface.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.core.models import Player
from src.core import constants

def generate_main_keyboard() -> InlineKeyboardMarkup:
    """
    Generates the main navigation inline keyboard for the bot.
    """
    markup = InlineKeyboardMarkup(row_width=3) # Adjust row_width as needed for layout
    buttons = []
    for button_data in constants.MAIN_KEYBOARD_BUTTONS:
        buttons.append(InlineKeyboardButton(button_data["text"], callback_data=button_data["callback_data"]))
    
    markup.add(*buttons)
    return markup

def generate_base_panel_message(player: Player) -> str:
    """
    Generates the text message for the /base panel, displaying player stats.
    """
    # Simulate current active timers (will be populated by scheduler later)
    # For now, just show placeholders or actual data if available
    ongoing_activities = []
    if player.current_quest_id != "tutorial_completed": # Assuming this is a state after onboarding
        ongoing_activities.append(f"• Complete quest: {player.current_quest_id}")
    # Placeholder for future:
    # if player.building_timer > 0: ongoing_activities.append(f"• Upgrade Barracks → Lv {player.barracks_level + 1} ({player.building_timer}m)")
    # if player.research_timer > 0: ongoing_activities.append(f"• Research Mine Efficiency II ({player.research_timer}m)")
    # if player.training_timer > 0: ongoing_activities.append(f"• Train {player.units_in_queue} Infantry ({player.training_timer}m)")
    # if player.attack_incoming_timer > 0: ongoing_activities.append(f"• Incoming Attack (Arrives in {player.attack_incoming_timer}m)")

    ongoing_str = "\n".join(ongoing_activities) if ongoing_activities else "  _No ongoing activities._"

    # Basic resource caps (will become dynamic later)
    resource_caps = {
        "wood": 5000,
        "stone": 5000,
        "food": 3000,
        "cash": 2000,
        "energy": 200,
        "diamonds": "∞" # Diamonds usually have no cap
    }

    message_text = f"""
🏠 Commander {player.commander_name}’s Base
Power: {player.power:,}  Prestige: {player.prestige}
Lv: {player.base_level} Base

Res: 🪵{player.wood:,}/{resource_caps["wood"]:,}  🪨{player.stone:,}/{resource_caps["stone"]:,}  🥖{player.food:,}/{resource_caps["food"]:,}  💰{player.cash:,}/{resource_caps["cash"]:,}  🔋{player.energy:,}/{resource_caps["energy"]:,}  💎{player.diamonds:,}
📈 Output/hr: +0🪵 +0🪨 +0🥖 +0💰 +0🔋  _(_*Placeholder*_ )_

🪖 Army: Infantry {player.infantry:,}, Tank {player.tank:,}, Artillery {player.artillery:,}, Destroyer {player.destroyer:,}

⏱ Ongoing:
{ongoing_str}

🎯 What's next, Commander?
"""
    return message_text