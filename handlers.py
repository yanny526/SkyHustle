# handlers.py
# Definitive Production Version - Re-architected for stability.

import logging
import math
import time
import json
from datetime import datetime, timedelta, timezone
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from functools import partial

import constants
import content
import google_sheets

logger = logging.getLogger(__name__)
user_state = {}

# --- This is the main registration function that sets up all bot behaviors ---
def register_handlers(bot, scheduler):

    # --- START COMMAND ---
    @bot.message_handler(commands=['start'])
    def start_handler(message: Message):
        """
        Handles the /start command. This is the entry point for all players.
        """
        user_id = message.from_user.id
        logger.info(f"Received /start from user_id: {user_id}")
        
        # We know this database call works from our diagnostic test.
        _, player_data = google_sheets.find_player_row(user_id)
        
        if player_data:
            # For returning players, show the main base panel.
            send_base_panel(bot, user_id, player_data)
        else:
            # For new players, start the onboarding conversation.
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            # Set the bot to expect the player's chosen name next.
            user_state[user_id] = partial(get_commander_name_handler, bot)

    # --- ONBOARDING & STATE-BASED HANDLERS ---
    def get_commander_name_handler(bot, message: Message):
        """
        Handles the message received after a new player is asked for their name.
        """
        user_id = message.from_user.id
        commander_name = message.text.strip()
        
        # Clean up the user's state so they're not stuck in this conversation.
        if user_id in user_state:
            del user_state[user_id]

        # Validation
        if not (3 <= len(commander_name) <= constants.ALLIANCE_CONFIG['name_max_length']):
            bot.send_message(user_id, f"A commander's name must be between 3 and {constants.ALLIANCE_CONFIG['name_max_length']} characters. Please try /start again.")
            return

        # Assemble the new player's data record.
        new_player_data = {
            **constants.INITIAL_PLAYER_STATS,
            constants.FIELD_USER_ID: user_id,
            constants.FIELD_COMMANDER_NAME: commander_name,
        }
        
        # Attempt to create the player in the database.
        if google_sheets.create_player_row(new_player_data):
            welcome_message = content.get_new_player_welcome_success_text(commander_name)
            bot.send_message(user_id, welcome_message, parse_mode='HTML')
            # Show the new player their base panel for the first time.
            send_base_panel(bot, user_id, new_player_data)
        else:
            bot.send_message(user_id, "A critical error occurred while creating your commander profile. Please contact support.")

    # --- DEFAULT MESSAGE HANDLER ---
    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        """
        This handler catches any message that isn't a specific command.
        It first checks if we are expecting a specific input from the user.
        If not, it treats the message as a main menu button press.
        """
        # If we are waiting for a specific input (e.g., a name), call the stored function.
        if message.from_user.id in user_state:
            user_state[message.from_user.id](message=message)
        else:
            # Otherwise, handle it as a menu button press.
            handle_menu_buttons(bot, message)

    def handle_menu_buttons(bot, message: Message):
        """Routes main menu button presses to the correct function."""
        if message.text == constants.MENU_BASE:
            _, player_data = google_sheets.find_player_row(message.from_user.id)
            if player_data:
                send_base_panel(bot, message.from_user.id, player_data)
        else:
            # For all other buttons, for now, just acknowledge them.
            bot.send_message(message.chat.id, f"The **{message.text}** system is under construction.", parse_mode="Markdown")


# --- UI-GENERATING HELPER FUNCTIONS ---
def send_base_panel(bot, user_id, player_data):
    """Constructs and sends the main base panel to the player."""
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def get_main_menu_keyboard():
    """Constructs and returns the main navigation keyboard."""
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [
        KeyboardButton(constants.MENU_BASE),
        KeyboardButton(constants.MENU_BUILD),
        KeyboardButton(constants.MENU_TRAIN),
        KeyboardButton(constants.MENU_RESEARCH),
        KeyboardButton(constants.MENU_ATTACK),
        KeyboardButton(constants.MENU_QUESTS),
        KeyboardButton(constants.MENU_SHOP),
        KeyboardButton(constants.MENU_PREMIUM),
        KeyboardButton(constants.MENU_MAP),
        KeyboardButton(constants.MENU_ALLIANCE),
    ]
    markup.add(*buttons)
    return markup