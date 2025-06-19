# handlers.py
# System 3 Finalization: Implements the complete training scheduler and logic.

import logging
import math
import time
from datetime import datetime, timedelta, timezone
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from functools import partial

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

# --- SCHEDULER COMPLETION JOBS ---
def complete_upgrade_job(bot, user_id, building_key):
    """The function that APScheduler executes when a construction timer finishes."""
    logger.info(f"Executing complete_upgrade_job for user {user_id}, building: {building_key}")
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return

    building_info = constants.BUILDING_DATA[building_key]
    building_level_field = building_info['id']
    current_level = int(player_data.get(building_level_field, 0))
    
    updates = {
        building_level_field: current_level + 1,
        'build_queue_item_id': '', 'build_queue_finish_time': ''
    }
    
    effect = building_info.get('effects', {})
    if effect.get('type') == 'production':
        rate_field = effect['resource']
        current_rate = int(player_data.get(rate_field, 0))
        updates[rate_field] = current_rate + effect['value_per_level']
    elif effect.get('type') == 'storage':
        value = effect['value_per_level']
        for res in ['wood', 'stone', 'iron', 'food']:
            updates[f'{res}_storage_cap'] = int(player_data.get(f'{res}_storage_cap', 0)) + value

    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Construction complete! Your **{building_info['name']}** has been upgraded to **Level {current_level + 1}**.")

def complete_training_job(bot, user_id, unit_key, quantity):
    """The function that APScheduler executes when a training timer finishes."""
    logger.info(f"Executing complete_training_job for user {user_id}, unit: {unit_key}, quantity: {quantity}")
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return

    unit_info = constants.UNIT_DATA[unit_key]
    unit_count_field = unit_info['id']
    current_units = int(player_data.get(unit_count_field, 0))
    current_power = int(player_data.get('power', 0))
    
    updates = {
        unit_count_field: current_units + quantity,
        'power': current_power + (unit_info['stats']['power'] * quantity),
        'train_queue_item_id': '',
        'train_queue_quantity': '',
        'train_queue_finish_time': ''
    }

    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Training complete! **{quantity}x {unit_info['name']}** {unit_info['emoji']} have joined your army.")

# --- MAIN HANDLER REGISTRATION ---
def register_handlers(bot, scheduler):
    
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        # This handler is stable and requires no changes.
        user_id = message.from_user.id
        row_index, player_data = google_sheets.find_player_row(user_id)
        if player_data: send_base_panel(bot, user_id, player_data)
        else:
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            user_state[user_id] = partial(get_commander_name_handler, bot)

    def get_commander_name_handler(bot, message: Message):
        # This handler is stable and requires no changes.
        user_id = message.from_user.id
        commander_name = message.text.strip()
        if not (3 <= len(commander_name) <= 20):
            bot.send_message(user_id, "A commander's name must be between 3 and 20 characters."); return
        new_player_data = {**constants.INITIAL_PLAYER_STATS, constants.FIELD_USER_ID: user_id, constants.FIELD_COMMANDER_NAME: commander_name}
        if google_sheets.create_player_row(new_player_data):
            welcome_message = content.get_new_player_welcome_success_text(commander_name)
            bot.send_message(user_id, welcome_message, parse_mode='HTML')
            send_base_panel(bot, user_id, new_player_data)
            if user_id in user_state: del user_state[user_id]
        else: bot.send_message(user_id, "A critical error occurred.")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        # This function is stable and requires no changes.
        user_id = call.from_user.id
        action = call.data
        logger.info(f"User {user_id} clicked inline button: {action}")
        bot.answer_callback_query(call.id)
        
        if action == 'back_to_base':
            row_index, player_data = google_sheets.find_player_row(user_id)
            if player_data:
                base_text = content.get_base_panel_text(player_data)
                bot.edit_message_text(base_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        elif action.startswith('build_'):
            building_key = action.split('_')[1]
            handle_upgrade_request(bot, scheduler, user_id, building_key, call.message)
        elif action.startswith('train_'):
            unit_key = action.split('_')[1]
            bot.edit_message_text("How many units would you like to train?", chat_id=call.message.chat.id, message_id=call.message.message_id)
            user_state[user_id] = partial(handle_train_quantity, bot, scheduler, unit_key)

    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        # This handler is stable and requires no changes.
        if message.from_user.id in user_state:
            user_state[message.from_user.id](message=message)
        else:
            handle_menu_buttons(bot, message)

    def handle_menu_buttons(bot, message: Message):
        # This handler is stable and requires no changes.
        if message.text == constants.MENU_BASE:
            row_index, player_data = google_sheets.find_player_row(message.from_user.id)
            if player_data: send_base_panel(bot, message.from_user.id, player_data)
        elif message.text == constants.MENU_BUILD:
            send_build_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_TRAIN:
            send_train_menu(bot, message.from_user.id)
        else:
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
            bot.send_message(message.chat.id, f"The **{message.text}** system is not yet online.", reply_markup=markup, parse_mode='Markdown')

def handle_upgrade_request(bot, scheduler, user_id, building_key, message):
    # This handler is stable and requires no changes.
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    if player_data.get('build_queue_item_id'): bot.answer_callback_query(message.id, "Builder is busy."); return
    building_info = constants.BUILDING_DATA[building_key]
    level = int(player_data.get(building_info['id'], 0))
    cost = calculate_cost(building_info['base_cost'], building_info['cost_multiplier'], level + 1)
    for res, amount in cost.items():
        if int(player_data.get(res, 0)) < amount: bot.send_message(user_id, f"⚠️ Insufficient resources."); return
    construction_time = calculate_time(building_info['base_time_seconds'], building_info['time_multiplier'], level + 1)
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=construction_time)
    new_resources = {res: int(player_data.get(res, 0)) - amount for res, amount in cost.items()}
    db_updates = {**new_resources, 'build_queue_item_id': building_key, 'build_queue_finish_time': finish_time.isoformat()}
    if google_sheets.update_player_data(user_id, db_updates):
        scheduler.add_job(complete_upgrade_job, 'date', run_date=finish_time, args=[bot, user_id, building_key], id=f'upgrade_{user_id}_{time.time()}')
        bot.edit_message_text(f"✅ Upgrade started! Your **{building_info['name']}** will reach **Level {level + 1}** in {timedelta(seconds=construction_time)}.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML')

# --- FULLY IMPLEMENTED TRAINING LOGIC ---

def handle_train_quantity(bot, scheduler, unit_key, message):
    """Handles the user's input for how many units to train and starts the job."""
    user_id = message.from_user.id
    
    # 1. Validate Input
    try:
        quantity = int(message.text)
        if quantity <= 0: raise ValueError
    except ValueError:
        bot.send_message(user_id, "Invalid quantity. Please enter a positive number.")
        user_state[user_id] = partial(handle_train_quantity, bot, scheduler, unit_key)
        return
    finally:
        if user_id in user_state: del user_state[user_id] # Clean up state

    # 2. Fetch Fresh Data & Check Queue
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: bot.send_message(user_id, "Error: Could not find your data."); return
    if player_data.get('train_queue_item_id'): bot.send_message(user_id, "⚠️ Your Barracks are already training units."); return

    # 3. Calculate Cost & Check Resources
    unit_info = constants.UNIT_DATA[unit_key]
    total_cost = {res: amount * quantity for res, amount in unit_info['cost'].items()}
    
    has_enough_resources = True
    missing_res_str = ""
    for resource, amount in total_cost.items():
        if int(player_data.get(resource, 0)) < amount:
            has_enough_resources = False
            missing_res_str += f"{amount:,} {resource.capitalize()}, "
            
    if not has_enough_resources:
        bot.send_message(user_id, f"⚠️ Insufficient resources. You need: {missing_res_str.strip(', ')}.")
        return

    # 4. All Checks Passed. Start Training.
    total_training_time_seconds = unit_info['train_time_seconds'] * quantity
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=total_training_time_seconds)
    
    new_resources = {res: int(player_data.get(res, 0)) - amount for res, amount in total_cost.items()}
    
    db_updates = {
        **new_resources,
        'train_queue_item_id': unit_key,
        'train_queue_quantity': quantity,
        'train_queue_finish_time': finish_time.isoformat()
    }

    if google_sheets.update_player_data(user_id, db_updates):
        # 5. Schedule Completion Job
        scheduler.add_job(
            complete_training_job,
            trigger='date',
            run_date=finish_time,
            args=[bot, user_id, unit_key, quantity],
            id=f'train_{user_id}_{unit_key}_{time.time()}' # Unique job ID
        )
        bot.send_message(user_id, f"✅ Training started! **{quantity}x {unit_info['name']}** {unit_info['emoji']} will be ready in {timedelta(seconds=total_training_time_seconds)}.")
    else:
        bot.send_message(user_id, "⚠️ An error occurred while starting training. Please try again.")

def send_train_menu(bot, user_id):
    """Displays the interactive training menu, checking prerequisites and queue status."""
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    
    if int(player_data.get('building_barracks_level', 0)) < 1:
        bot.send_message(user_id, "A 🪖 **Barracks** is required to train units.\n\nConstruct one from the **'⚒️ Build'** menu first.", parse_mode="Markdown")
        return

    markup = InlineKeyboardMarkup(row_width=1)
    if train_item_id := player_data.get('train_queue_item_id'):
        finish_time = datetime.fromisoformat(player_data.get('train_queue_finish_time'))
        remaining = finish_time - datetime.now(timezone.utc)
        unit_name = constants.UNIT_DATA[train_item_id]['name']
        quantity = player_data.get('train_queue_quantity')
        text = f"<b><u>🪖 Barracks (Training)</u></b>\n\nYour barracks are busy training **{quantity}x {unit_name}**. Time remaining: {str(timedelta(seconds=int(remaining.total_seconds())))}."
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    else:
        text = f"<b><u>🪖 Barracks (Idle)</u></b>\nSelect a unit to train:\n"
        for key, info in constants.UNIT_DATA.items():
            if int(player_data.get('building_barracks_level', 0)) >= info['required_barracks_level']:
                cost_str = " | ".join([f"{v:,} {res.capitalize()}" for res, v in info['cost'].items()])
                text += f"\n{info['emoji']} <b>{info['name']}</b> (ATK:{info['stats']['attack']}/DEF:{info['stats']['defense']})"
                markup.add(InlineKeyboardButton(f"Train - {cost_str} / unit", callback_data=f"train_{key}"))
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
        
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

# These final two functions are stable and require no changes
def send_base_panel(bot, user_id, player_data):
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def get_main_menu_keyboard():
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(b) for b in [constants.MENU_BASE, constants.MENU_BUILD, constants.MENU_TRAIN, constants.MENU_RESEARCH, constants.MENU_ATTACK, constants.MENU_QUESTS, constants.MENU_SHOP, constants.MENU_PREMIUM, constants.MENU_MAP, constants.MENU_ALLIANCE]]
    markup.add(*buttons)
    return markup