# handlers.py
# System 2 Finalization: Implements the complete construction logic.

import logging
import math
import time
from datetime import datetime, timedelta, timezone
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

import constants
import content
import google_sheets

logger = logging.getLogger(__name__)
user_state = {}

# --- HELPER FUNCTIONS ---
def calculate_cost(base_cost, multiplier, level):
    return {res: math.floor(amount * (multiplier ** (level - 1))) for res, amount in base_cost.items()}

def calculate_time(base_time, multiplier, level):
    return math.floor(base_time * (multiplier ** (level - 1)))

# --- COMPLETION JOB ---
def complete_upgrade_job(bot, user_id, building_key):
    """The function that APScheduler will execute when a construction timer finishes."""
    logger.info(f"Executing complete_upgrade_job for user {user_id}, building: {building_key}")
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data:
        logger.error(f"Cannot complete upgrade for user {user_id}, player data not found.")
        return

    building_info = constants.BUILDING_DATA[building_key]
    building_level_field = building_info['id']
    current_level = int(player_data.get(building_level_field, 0))
    
    updates = {
        building_level_field: current_level + 1,
        'build_queue_item_id': '',
        'build_queue_finish_time': ''
    }
    
    # Apply effects of the upgrade
    effect = building_info.get('effects', {})
    if effect.get('type') == 'production':
        rate_field = effect['resource']
        current_rate = int(player_data.get(rate_field, 0))
        updates[rate_field] = current_rate + effect['value_per_level']
    elif effect.get('type') == 'storage':
        value = effect['value_per_level']
        updates['wood_storage_cap'] = int(player_data.get('wood_storage_cap', 0)) + value
        updates['stone_storage_cap'] = int(player_data.get('stone_storage_cap', 0)) + value
        updates['iron_storage_cap'] = int(player_data.get('iron_storage_cap', 0)) + value
        updates['food_storage_cap'] = int(player_data.get('food_storage_cap', 0)) + value

    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Construction complete! Your **{building_info['name']}** has been upgraded to **Level {current_level + 1}**.")
    else:
        bot.send_message(user_id, f"⚠️ An error occurred while completing your **{building_info['name']}** upgrade. Please contact support.")

# --- MAIN HANDLER REGISTRATION ---
def register_handlers(bot, scheduler):
    
    # --- START & ONBOARDING (Unchanged) ---
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        user_id = message.from_user.id
        row_index, player_data = google_sheets.find_player_row(user_id)
        if player_data: send_base_panel(bot, user_id, player_data)
        else:
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            user_state[user_id] = lambda msg: get_commander_name_handler(bot, msg)
            
    def get_commander_name_handler(bot, message: Message):
        user_id = message.from_user.id
        commander_name = message.text.strip()
        if not (3 <= len(commander_name) <= 20):
            bot.send_message(user_id, "A commander's name must be between 3 and 20 characters.")
            return
        new_player_data = { **constants.INITIAL_PLAYER_STATS, FIELD_USER_ID: user_id, FIELD_COMMANDER_NAME: commander_name }
        if google_sheets.create_player_row(new_player_data):
            welcome_message = content.get_new_player_welcome_success_text(commander_name)
            bot.send_message(user_id, welcome_message, parse_mode='HTML')
            send_base_panel(bot, user_id, new_player_data)
            if user_id in user_state: del user_state[user_id]
        else: bot.send_message(user_id, "A critical error occurred. Please try /start again later.")

    # --- CALLBACK HANDLER (FOR BUTTONS) ---
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id = call.from_user.id
        action = call.data
        
        if action == 'back_to_base':
            row_index, player_data = google_sheets.find_player_row(user_id)
            if player_data:
                base_text = content.get_base_panel_text(player_data)
                bot.edit_message_text(base_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        elif action.startswith('build_'):
            building_key = action.split('_')[1]
            handle_upgrade_request(bot, scheduler, user_id, building_key)
        
        bot.answer_callback_query(call.id)

    # --- MENU & MESSAGE HANDLERS ---
    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        if message.from_user.id in user_state:
            user_state[message.from_user.id](message)
        else:
            handle_menu_buttons(bot, message)

    def handle_menu_buttons(bot, message: Message):
        if message.text == constants.MENU_BASE:
            row_index, player_data = google_sheets.find_player_row(message.from_user.id)
            if player_data: send_base_panel(bot, message.from_user.id, player_data)
        elif message.text == constants.MENU_BUILD:
            send_build_menu(bot, message.from_user.id)
        else:
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
            bot.send_message(message.chat.id, f"The **{message.text}** system is not yet online.", reply_markup=markup, parse_mode='Markdown')

# --- BUILD LOGIC ---
def handle_upgrade_request(bot, scheduler, user_id, building_key):
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data:
        bot.send_message(user_id, "Error: Player data not found.")
        return

    # 1. Check if builder is busy
    if player_data.get('build_queue_item_id'):
        bot.send_message(user_id, "⚠️ Your construction yard is busy. Please wait for the current upgrade to complete.")
        return

    building_info = constants.BUILDING_DATA[building_key]
    current_level = int(player_data.get(building_info['id'], 0))
    next_level = current_level + 1

    # 2. Calculate cost and check resources
    cost = calculate_cost(building_info['base_cost'], building_info['cost_multiplier'], next_level)
    has_enough_resources = True
    missing_res_str = ""
    for resource, amount in cost.items():
        if int(player_data.get(resource, 0)) < amount:
            has_enough_resources = False
            missing_res_str += f"{amount:,} {resource.capitalize()}, "
    
    if not has_enough_resources:
        bot.send_message(user_id, f"⚠️ Insufficient resources. You need: {missing_res_str.strip(', ')}.")
        return

    # 3. All checks passed. Start the upgrade.
    construction_time_seconds = calculate_time(building_info['base_time_seconds'], building_info['time_multiplier'], next_level)
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=construction_time_seconds)
    
    new_resources = {res: int(player_data.get(res, 0)) - amount for res, amount in cost.items()}
    
    db_updates = {
        **new_resources,
        'build_queue_item_id': building_key,
        'build_queue_finish_time': finish_time.isoformat()
    }

    if google_sheets.update_player_data(user_id, db_updates):
        # 4. Schedule the completion job
        scheduler.add_job(
            complete_upgrade_job,
            trigger='date',
            run_date=finish_time,
            args=[bot, user_id, building_key],
            id=f'upgrade_{user_id}_{building_key}_{time.time()}' # Unique job ID
        )
        bot.send_message(user_id, f"✅ Upgrade started! Your **{building_info['name']}** will reach **Level {next_level}** in {timedelta(seconds=construction_time_seconds)}.")
    else:
        bot.send_message(user_id, "⚠️ An error occurred while starting the upgrade. Please try again.")

# --- UI SENDING FUNCTIONS ---
def send_base_panel(bot, user_id, player_data):
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def send_build_menu(bot, user_id):
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return

    # Check if a build is in progress to show a status
    if build_item_id := player_data.get('build_queue_item_id'):
        finish_time_str = player_data.get('build_queue_finish_time')
        finish_time = datetime.fromisoformat(finish_time_str)
        remaining = finish_time - datetime.now(timezone.utc)
        building_name = constants.BUILDING_DATA[build_item_id]['name']
        text = f"<b><u>⚒️ Construction Yard (Busy)</u></b>\n\n"
        text += f"Your **{building_name}** is currently being upgraded. Time remaining: {str(timedelta(seconds=int(remaining.total_seconds())))}."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
        bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)
        return
        
    text = "<b><u>⚒️ Construction Yard (Idle)</u></b>\nSelect a building to upgrade:\n\n"
    markup = InlineKeyboardMarkup(row_width=1)
    for key, info in constants.BUILDING_DATA.items():
        level = int(player_data.get(info['id'], 0))
        cost = calculate_cost(info['base_cost'], info['cost_multiplier'], level + 1)
        cost_str = " | ".join([f"{v:,} {k.capitalize()}" for k, v in cost.items()])
        markup.add(InlineKeyboardButton(f"{info['emoji']} {info['name']} (Lv. {level})", callback_data=f"info_{key}")) # Placeholder for info
        markup.add(InlineKeyboardButton(f"Upgrade - Cost: {cost_str}", callback_data=f"build_{key}"))

    markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

def get_main_menu_keyboard():
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(b) for b in [constants.MENU_BASE, constants.MENU_BUILD, constants.MENU_TRAIN, constants.MENU_RESEARCH, constants.MENU_ATTACK, constants.MENU_QUESTS, constants.MENU_SHOP, constants.MENU_PREMIUM, constants.MENU_MAP, constants.MENU_ALLIANCE]]
    markup.add(*buttons)
    return markup