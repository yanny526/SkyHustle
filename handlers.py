# handlers.py
# Final hotfix for NameError in send_build_menu.

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

# --- SECTION 1: UTILITY & CALCULATION HELPERS ---

def calculate_cost(base_cost, multiplier, level):
    return {res: math.floor(amount * (multiplier ** (level - 1))) for res, amount in base_cost.items()}

def calculate_time(base_time, multiplier, level):
    return math.floor(base_time * (multiplier ** (level - 1)))

def get_main_menu_keyboard():
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(b) for b in [constants.MENU_BASE, constants.MENU_BUILD, constants.MENU_TRAIN, constants.MENU_RESEARCH, constants.MENU_ATTACK, constants.MENU_QUESTS, constants.MENU_SHOP, constants.MENU_PREMIUM, constants.MENU_MAP, constants.MENU_ALLIANCE]]
    markup.add(*buttons)
    return markup


# --- SECTION 2: SCHEDULER COMPLETION JOBS ---

def complete_upgrade_job(bot, user_id, building_key):
    # This function is correct and unchanged.
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
    # This function is correct and unchanged.
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
        'train_queue_item_id': '', 'train_queue_quantity': '', 'train_queue_finish_time': ''
    }
    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Training complete! **{quantity}x {unit_info['name']}** {unit_info['emoji']} have joined your army.")


# --- SECTION 3: UI-GENERATING & CORE LOGIC FUNCTIONS ---

def send_base_panel(bot, user_id, player_data):
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def send_build_menu(bot, user_id):
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    if build_item_id := player_data.get('build_queue_item_id'):
        finish_time = datetime.fromisoformat(player_data.get('build_queue_finish_time'))
        remaining = finish_time - datetime.now(timezone.utc)
        building_name = constants.BUILDING_DATA[build_item_id]['name']
        text = f"<b><u>⚒️ Construction Yard (Busy)</u></b>\n\nYour **{building_name}** is upgrading. Time left: {str(timedelta(seconds=int(remaining.total_seconds())))}."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
        bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)
        return
    text = "<b><u>⚒️ Construction Yard (Idle)</u></b>\nSelect a building to upgrade:\n\n"
    markup = InlineKeyboardMarkup(row_width=1)
    for key, info in constants.BUILDING_DATA.items():
        level = int(player_data.get(info['id'], 0))
        cost = calculate_cost(info['base_cost'], info['cost_multiplier'], level + 1)
        
        # --- THIS IS THE CORRECTED LINE ---
        cost_str = " | ".join([f"{v:,} {k.capitalize()}" for k, v in cost.items()])
        # The old line incorrectly used 'res' instead of 'k'
        
        text += f"{info['emoji']} <b>{info['name']}</b> (Level {level})"
        markup.add(InlineKeyboardButton(f"Upgrade - Cost: {cost_str}", callback_data=f"build_{key}"))
    markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

def send_train_menu(bot, user_id):
    # This function is correct and unchanged.
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

def handle_upgrade_request(bot, scheduler, user_id, building_key, message):
    # This function is correct and unchanged.
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    if player_data.get('build_queue_item_id'): return
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

def handle_train_quantity(bot, scheduler, unit_key, message):
    # This function is correct and unchanged.
    user_id = message.from_user.id
    try: quantity = int(message.text)
    except ValueError: bot.send_message(user_id, "Invalid quantity."); return
    finally:
        if user_id in user_state: del user_state[user_id]
    if quantity <= 0: return
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data or player_data.get('train_queue_item_id'): return
    unit_info = constants.UNIT_DATA[unit_key]
    total_cost = {res: amount * quantity for res, amount in unit_info['cost'].items()}
    for resource, amount in total_cost.items():
        if int(player_data.get(resource, 0)) < amount: bot.send_message(user_id, f"⚠️ Insufficient resources."); return
    total_training_time = unit_info['train_time_seconds'] * quantity
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=total_training_time)
    new_resources = {res: int(player_data.get(res, 0)) - amount for res, amount in total_cost.items()}
    db_updates = {**new_resources, 'train_queue_item_id': unit_key, 'train_queue_quantity': quantity, 'train_queue_finish_time': finish_time.isoformat()}
    if google_sheets.update_player_data(user_id, db_updates):
        scheduler.add_job(complete_training_job, 'date', run_date=finish_time, args=[bot, user_id, unit_key, quantity], id=f'train_{user_id}_{time.time()}')
        bot.send_message(user_id, f"✅ Training started! **{quantity}x {unit_info['name']}** {unit_info['emoji']} will be ready in {timedelta(seconds=total_training_time)}.")


# --- SECTION 4: MAIN HANDLER REGISTRATION ---
# This entire section is correct and unchanged.

def register_handlers(bot, scheduler):
    
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        user_id = message.from_user.id
        row_index, player_data = google_sheets.find_player_row(user_id)
        if player_data: send_base_panel(bot, user_id, player_data)
        else:
            welcome_text = content.get_welcome_new_player_text()
            bot.send_message(user_id, welcome_text, parse_mode='HTML')
            user_state[user_id] = partial(get_commander_name_handler, bot)

    def get_commander_name_handler(bot, message: Message):
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

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id = call.from_user.id
        action = call.data
        logger.info(f"User {user_id} clicked inline button: {action}")
        bot.answer_callback_query(call.id)
        if action == 'back_to_base':
            row_index, player_data = google_sheets.find_player_row(user_id)
            if player_data: bot.edit_message_text(content.get_base_panel_text(player_data), call.message.chat.id, call.message.message_id, parse_mode='HTML')
        elif action.startswith('build_'):
            building_key = action.split('_')[1]
            handle_upgrade_request(bot, scheduler, user_id, building_key, call.message)
        elif action.startswith('train_'):
            unit_key = action.split('_')[1]
            bot.edit_message_text("How many units would you like to train?", chat_id=call.message.chat.id, message_id=call.message.message_id)
            user_state[user_id] = partial(handle_train_quantity, bot, scheduler, unit_key)

    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        if message.from_user.id in user_state:
            user_state[message.from_user.id](message=message)
        else:
            handle_menu_buttons(bot, message)

    def handle_menu_buttons(bot, message: Message):
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