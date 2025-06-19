# handlers.py
# The command and control center for all user interactions.
# Upgraded to handle dynamic inline keyboards for a fluid, app-like user experience.

import logging
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone

# Import our engineered modules
import constants
import content
import google_sheets

logger = logging.getLogger(__name__)

user_state = {}

def register_handlers(bot):
    """Registers all message, command, and callback handlers with the TeleBot instance."""

    # --- Command Handlers ---
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        """Handles the primary /start command, the gateway for all users."""
        user_id = message.from_user.id
        logger.info(f"Received /start command from user_id: {user_id}")
        
        row_index, player_data = google_sheets.find_player_row(user_id)
        
        if player_data:
            # --- Logic for a RETURNING Player ---
            send_base_panel(bot, user_id, player_data)
        else:
            # --- Logic for a NEW Player ---
            logger.info(f"New player detected: {user_id}. Starting onboarding.")
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            user_state[user_id] = get_commander_name_handler

    # --- State-Based & Default Handlers ---
    def get_commander_name_handler(message: Message):
        """Handles the message after a new player is asked for their name."""
        user_id = message.from_user.id
        commander_name = message.text.strip()
        
        if not commander_name or len(commander_name) > 20 or len(commander_name) < 3:
            bot.send_message(user_id, "A commander's name must be between 3 and 20 characters. Please choose another designation.")
            user_state[user_id] = get_commander_name_handler
            return

        logger.info(f"User {user_id} chose name: {commander_name}")
        new_player_data = {
            constants.FIELD_USER_ID: user_id,
            constants.FIELD_COMMANDER_NAME: commander_name,
            **constants.INITIAL_PLAYER_STATS
        }

        if google_sheets.create_player_row(new_player_data):
            logger.info(f"Successfully created player {commander_name} in Sheet.")
            welcome_message = content.get_new_player_welcome_success_text(commander_name)
            bot.send_message(user_id, welcome_message, parse_mode='HTML')
            send_base_panel(bot, user_id, new_player_data)
            if user_id in user_state: del user_state[user_id]
        else:
            logger.error(f"Failed to create player {commander_name} in Sheet.")
            bot.send_message(user_id, "A critical error occurred. Please try /start again later.")

    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        """The main message router, checking for state or menu clicks."""
        user_id = message.from_user.id
        
        if user_id in user_state:
            user_state[user_id](message)
        else:
            handle_menu_buttons(bot, message)

    # --- Callback Query Handler (for Inline Buttons) ---
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        """
        Handles all button clicks from Inline Keyboards.
        This is a core component of a modern Telegram bot UI.
        """
        user_id = call.from_user.id
        # The 'data' is the string we assigned to the button's callback_data.
        callback_action = call.data

        logger.info(f"User {user_id} clicked inline button with action: {callback_action}")

        if callback_action == 'back_to_base':
            # Find the player's data again
            row_index, player_data = google_sheets.find_player_row(user_id)
            if player_data:
                # Edit the existing message to show the base panel again. This feels seamless.
                base_panel_text = content.get_base_panel_text(player_data)
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=base_panel_text,
                    parse_mode='HTML'
                )
            else:
                # Handle edge case where data is lost
                bot.answer_callback_query(call.id, "Error: Player data not found.")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="An error occurred. Please try /start."
                )
        
        # Acknowledge the button click to remove the "loading" state on the user's client.
        bot.answer_callback_query(call.id)

# --- Helper Functions ---
def send_base_panel(bot, user_id, player_data):
    """A centralized function to send the main base panel."""
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def handle_menu_buttons(bot, message: Message):
    """Handles clicks on the main keyboard. Now uses inline buttons for sub-menus."""
    if message.text == constants.MENU_BASE:
        row_index, player_data = google_sheets.find_player_row(message.from_user.id)
        if player_data:
            send_base_panel(bot, message.from_user.id, player_data)
    elif message.text in [constants.MENU_BUILD, constants.MENU_TRAIN, constants.MENU_RESEARCH]:
        # Instead of a new message, we now send a placeholder with a "Back" inline button.
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
        
        bot.send_message(
            message.chat.id, 
            f"The **{message.text}** system is under construction, Commander. This menu will be built in System 2.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        bot.send_message(message.chat.id, f"The '{message.text}' system is not yet online.")

def get_main_menu_keyboard():
    """Constructs and returns the main navigation keyboard markup."""
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