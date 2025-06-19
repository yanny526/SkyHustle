# src/bot/handlers.py
import telebot
from telebot import TeleBot # Explicitly import TeleBot type hint for clarity
import time
import logging
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

from src.core.models import Player
from src.core import constants, content
from src.utils import google_sheets
from src.systems import user_interface

# Configure logging
logger = logging.getLogger(__name__)

# This dictionary will hold the next expected function for a user
# Key: user_id, Value: function to handle the next message
user_state = {}

def register_handlers(bot: TeleBot):
    """Registers all the command and message handlers for the bot."""
    
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        """Handles the /start command."""
        user_id = message.from_user.id
        logger.info(f"Received /start command from user_id: {user_id}")
        
        row_index, player_data = google_sheets.find_player_row(user_id)
        
        if player_data:
            # --- RETURNING PLAYER ---
            commander_name = player_data.get(constants.FIELD_COMMANDER_NAME, "Commander")
            logger.info(f"Returning player '{commander_name}' (user_id: {user_id}) found at row {row_index}.")
            
            base_panel_text = content.get_base_panel_text(player_data)
            markup = get_main_menu_keyboard()
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
        else:
            # --- NEW PLAYER ---
            logger.info(f"New player detected with user_id: {user_id}. Starting onboarding.")
            bot.send_message(user_id, content.WELCOME_NEW_PLAYER)
            # Set the next state for this user to expect their chosen name
            user_state[user_id] = get_commander_name_handler

    def get_commander_name_handler(message: Message):
        """Handles the message after the new player is asked for their name."""
        user_id = message.from_user.id
        commander_name = message.text.strip()
        
        # Basic validation for the name
        if not commander_name or len(commander_name) > 20:
            bot.send_message(user_id, "That's not a valid name, Commander. Please choose a name less than 20 characters.")
            user_state[user_id] = get_commander_name_handler # Ask again
            return

        logger.info(f"User {user_id} chose commander name: {commander_name}")

        # Create the new player data dictionary
        new_player_data = {
            constants.FIELD_USER_ID: user_id,
            constants.FIELD_COMMANDER_NAME: commander_name,
            **constants.INITIAL_PLAYER_STATS # Unpack the initial stats
        }

        # Create the player record in the Google Sheet
        if google_sheets.create_player_row(new_player_data):
            logger.info(f"Successfully created player {commander_name} in Google Sheet.")
            
            # Welcome the player and show their base
            welcome_message = content.get_new_player_welcome(commander_name)
            bot.send_message(user_id, welcome_message)
            
            base_panel_text = content.get_base_panel_text(new_player_data)
            markup = get_main_menu_keyboard()
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
            
            # Clear the state for the user
            if user_id in user_state:
                del user_state[user_id]
        else:
            logger.error(f"Failed to create player {commander_name} in Google Sheet.")
            bot.send_message(user_id, "A critical error occurred while establishing your command base. Please try /start again.")

    # A generic handler for all other text messages
    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        """
        The main message router. It checks the user's state or handles menu buttons.
        """
        user_id = message.from_user.id
        
        # If we are waiting for a specific input (like the commander name)
        if user_id in user_state:
            # Call the function we're waiting for
            handler_func = user_state[user_id]
            handler_func(message)
        else:
            # Otherwise, handle as a menu button click or unknown command
            handle_menu_buttons(message)

    def handle_menu_buttons(message: Message):
        """Handles clicks on the main menu keyboard."""
        user_id = message.from_user.id
        row_index, player_data = google_sheets.find_player_row(user_id)

        if not player_data:
            bot.send_message(user_id, "I don't have a record for you, Commander. Please use /start to begin.")
            return

        base_panel_text = content.get_base_panel_text(player_data)
        markup = get_main_menu_keyboard()
        
        # Simple placeholder logic for now
        if message.text == constants.MENU_BASE:
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
        elif message.text in [constants.MENU_BUILD, constants.MENU_MAP, constants.MENU_RESEARCH, constants.MENU_UNITS]:
            bot.send_message(user_id, content.UNDER_CONSTRUCTION)
            # Resend the base panel to keep the user experience smooth
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
        else:
            bot.send_message(user_id, "Unknown command, Commander. Please use the menu below.")
            bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def get_main_menu_keyboard():
    """Creates the main navigation keyboard."""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        KeyboardButton(constants.MENU_BASE),
        KeyboardButton(constants.MENU_BUILD),
        KeyboardButton(constants.MENU_MAP),
        KeyboardButton(constants.MENU_RESEARCH),
        KeyboardButton(constants.MENU_UNITS)
    ]
    markup.add(*buttons)
    return markup