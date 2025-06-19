# handlers.py
# The command and control center for all user interactions.
# System 2 Upgrade: Now includes the logic to display the interactive build menu.

import logging
import math
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Import our engineered modules
import constants
import content
import google_sheets

logger = logging.getLogger(__name__)
user_state = {}

def register_handlers(bot):
    """Registers all message, command, and callback handlers with the TeleBot instance."""

    # --- Command & State Handlers (from System 1) ---
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        user_id = message.from_user.id
        logger.info(f"Received /start command from user_id: {user_id}")
        row_index, player_data = google_sheets.find_player_row(user_id)
        if player_data:
            send_base_panel(bot, user_id, player_data)
        else:
            logger.info(f"New player detected: {user_id}. Starting onboarding.")
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            user_state[user_id] = get_commander_name_handler

    def get_commander_name_handler(message: Message):
        # This function remains unchanged from the previous version.
        user_id = message.from_user.id
        commander_name = message.text.strip()
        if not commander_name or len(commander_name) > 20 or len(commander_name) < 3:
            bot.send_message(user_id, "A commander's name must be between 3 and 20 characters.")
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
        user_id = message.from_user.id
        if user_id in user_state:
            user_state[user_id](message)
        else:
            handle_menu_buttons(bot, message)

    # --- Callback Query Handler (for Inline Buttons) ---
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id = call.from_user.id
        callback_action = call.data
        logger.info(f"User {user_id} clicked inline button with action: {callback_action}")

        if callback_action == 'back_to_base':
            # This logic remains from our UI polish pass
            row_index, player_data = google_sheets.find_player_row(user_id)
            if player_data:
                base_panel_text = content.get_base_panel_text(player_data)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=base_panel_text, parse_mode='HTML')
            else:
                bot.answer_callback_query(call.id, "Error: Player data not found.")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="An error occurred. Please try /start.")
        
        # --- NEW: Handle clicks on the 'Upgrade' buttons ---
        elif callback_action.startswith('build_'):
            # For now, we just acknowledge the click. The logic for this will be built in the next step.
            building_id = callback_action.split('_')[1]
            building_name = constants.BUILDING_DATA.get(building_id, {}).get('name', 'Unknown Building')
            bot.answer_callback_query(call.id, f"Upgrade for {building_name} acknowledged. Construction logic is next.")

        bot.answer_callback_query(call.id)


# --- Helper & UI Functions ---

def send_base_panel(bot, user_id, player_data):
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

# --- NEW: Build Menu Logic ---

def calculate_cost(base_cost, multiplier, level):
    """Calculates the resource cost for a given level."""
    cost = {}
    for resource, amount in base_cost.items():
        cost[resource] = math.floor(amount * (multiplier ** (level - 1)))
    return cost

def send_build_menu(bot, user_id):
    """Fetches player data and displays the interactive build menu."""
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data:
        bot.send_message(user_id, "Error: Could not retrieve your base data. Please try /start.")
        return

    text = "<b><u>⚒️ Construction Yard</u></b>\nSelect a building to upgrade:\n\n"
    markup = InlineKeyboardMarkup(row_width=1)

    for building_key, building_info in constants.BUILDING_DATA.items():
        current_level = int(player_data.get(building_info['id'], 0))
        next_level = current_level + 1
        
        cost = calculate_cost(building_info['base_cost'], building_info['cost_multiplier'], next_level)
        cost_str = " | ".join([f"{v:,} {k.capitalize()}" for k, v in cost.items()])
        
        button_text = f"Upgrade to Lv. {next_level} - Cost: {cost_str}"
        # The callback_data is a command for our bot, e.g., 'build_hq'
        callback_data = f"build_{building_key}"
        
        text += f"{building_info['emoji']} <b>{building_info['name']}</b> (Level {current_level})\n"
        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))

    # Add a "Back to Base" button at the end
    markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

def handle_menu_buttons(bot, message: Message):
    """Handles clicks on the main keyboard."""
    if message.text == constants.MENU_BASE:
        row_index, player_data = google_sheets.find_player_row(message.from_user.id)
        if player_data:
            send_base_panel(bot, message.from_user.id, player_data)
            
    elif message.text == constants.MENU_BUILD:
        # --- THIS IS THE UPGRADED PART ---
        send_build_menu(bot, message.from_user.id)
        
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
        bot.send_message(message.chat.id, f"The **{message.text}** system is under construction.", reply_markup=markup, parse_mode='Markdown')

def get_main_menu_keyboard():
    """Constructs and returns the main navigation keyboard markup."""
    # This function remains unchanged.
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [
        KeyboardButton(constants.MENU_BASE), KeyboardButton(constants.MENU_BUILD),
        KeyboardButton(constants.MENU_TRAIN), KeyboardButton(constants.MENU_RESEARCH),
        KeyboardButton(constants.MENU_ATTACK), KeyboardButton(constants.MENU_QUESTS),
        KeyboardButton(constants.MENU_SHOP), KeyboardButton(constants.MENU_PREMIUM),
        KeyboardButton(constants.MENU_MAP), KeyboardButton(constants.MENU_ALLIANCE),
    ]
    markup.add(*buttons)
    return markup