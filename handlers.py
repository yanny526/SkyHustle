 # handlers.py
# The command and control center for all user interactions.
# This module acts as the bot's "brain," processing commands and managing user state.

import logging
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timezone

# Import our engineered modules
import constants
import content
import google_sheets

logger = logging.getLogger(__name__)

# A simple, yet powerful, in-memory state machine.
# Key: user_id, Value: the function to handle the user's next message.
# This is a superior method for managing multi-step conversations.
user_state = {}

def register_handlers(bot):
    """
    Registers all message and command handlers with the TeleBot instance.
    This is the master function that connects our logic to the bot.
    """

    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        """Handles the primary /start command, the gateway for all users."""
        user_id = message.from_user.id
        logger.info(f"Received /start command from user_id: {user_id}")
        
        # Check our database to see if this commander is already known to us.
        row_index, player_data = google_sheets.find_player_row(user_id)
        
        if player_data:
            # --- Logic for a RETURNING Player ---
            commander_name = player_data.get(constants.FIELD_COMMANDER_NAME, "Commander")
            logger.info(f"Returning player '{commander_name}' (user_id: {user_id}) found at row {row_index}.")
            
            base_panel_text = content.get_base_panel_text(player_data)
            markup = get_main_menu_keyboard()
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
        else:
            # --- Logic for a NEW Player ---
            logger.info(f"New player detected with user_id: {user_id}. Starting onboarding protocol.")
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            # Set the next expected state for this user to be the name handler.
            user_state[user_id] = get_commander_name_handler

    def get_commander_name_handler(message: Message):
        """Handles the message after a new player is asked for their name."""
        user_id = message.from_user.id
        # Sanitize input for safety and consistency.
        commander_name = message.text.strip()
        
        # Input validation is a mark of quality.
        if not commander_name or len(commander_name) > 20 or len(commander_name) < 3:
            bot.send_message(user_id, "A commander's name must be between 3 and 20 characters. Please choose another designation.")
            user_state[user_id] = get_commander_name_handler # Re-prompt by keeping the state.
            return

        logger.info(f"User {user_id} chose commander name: {commander_name}")

        # Assemble the complete data record for the new player.
        new_player_data = {
            constants.FIELD_USER_ID: user_id,
            constants.FIELD_COMMANDER_NAME: commander_name,
            **constants.INITIAL_PLAYER_STATS # Unpack all initial stats from our constants file.
        }

        # Attempt to create the player record in our database.
        if google_sheets.create_player_row(new_player_data):
            logger.info(f"Successfully created player {commander_name} in Google Sheet.")
            
            welcome_message = content.get_new_player_welcome_success_text(commander_name)
            bot.send_message(user_id, welcome_message, parse_mode='HTML')
            
            # Immediately show them their new base.
            base_panel_text = content.get_base_panel_text(new_player_data)
            markup = get_main_menu_keyboard()
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
            
            # Onboarding complete. Clear the state for this user.
            if user_id in user_state:
                del user_state[user_id]
        else:
            logger.error(f"Failed to create player {commander_name} in Google Sheet for user_id {user_id}.")
            bot.send_message(user_id, "A critical error occurred while establishing your command base. Please contact support or try /start again later.")

    # A generic handler for all other text messages. This acts as a router.
    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        """
        The main message router. It first checks if the user is in a specific state
        (like naming their commander) before handling menu button clicks.
        """
        user_id = message.from_user.id
        
        if user_id in user_state:
            # If we are waiting for a specific input, call the designated handler function.
            handler_func = user_state[user_id]
            handler_func(message)
        else:
            # Otherwise, handle as a standard menu button click.
            handle_menu_buttons(bot, message)

def handle_menu_buttons(bot, message: Message):
    """Handles clicks on the main menu keyboard. For now, it's a placeholder."""
    # This function will be expanded dramatically in future systems.
    bot.send_message(message.chat.id, f"The '{message.text}' system is not yet online, Commander.")

def get_main_menu_keyboard():
    """Constructs and returns the main navigation keyboard markup. A reusable utility."""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
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