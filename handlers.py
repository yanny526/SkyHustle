# handlers.py
# System 3 Upgrade: Implements the interactive training menu and workflow.

import logging
import math
import time
from datetime import datetime, timedelta, timezone
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from functools import partial # A tool for creating specialized function versions

import constants
import content
import google_sheets

logger = logging.getLogger(__name__)
user_state = {}

# All helper functions (calculate_cost, calculate_time, complete_upgrade_job) are unchanged.
# For brevity, I will omit them here, but ensure they are in your file.
# Your register_handlers and all previous handler functions also remain.
# The key changes are in handle_menu_buttons, handle_callback_query, and the new training functions.

# To ensure perfection, please replace the entire file's content with this:

def calculate_cost(base_cost, multiplier, level):
    return {res: math.floor(amount * (multiplier ** (level - 1))) for res, amount in base_cost.items()}

def calculate_time(base_time, multiplier, level):
    return math.floor(base_time * (multiplier ** (level - 1)))

def complete_upgrade_job(bot, user_id, building_key):
    # This function remains unchanged
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
    else:
        bot.send_message(user_id, f"⚠️ Error completing your **{building_info['name']}** upgrade.")

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
            bot.send_message(user_id, "A commander's name must be between 3 and 20 characters.")
            return
        new_player_data = {
            **constants.INITIAL_PLAYER_STATS,
            constants.FIELD_USER_ID: user_id,
            constants.FIELD_COMMANDER_NAME: commander_name
        }
        if google_sheets.create_player_row(new_player_data):
            welcome_message = content.get_new_player_welcome_success_text(commander_name)
            bot.send_message(user_id, welcome_message, parse_mode='HTML')
            send_base_panel(bot, user_id, new_player_data)
            if user_id in user_state: del user_state[user_id]
        else: bot.send_message(user_id, "A critical error occurred.")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id = call.from_user.id
        action = call.data
        logger.info(f"User {user_id} clicked inline button: {action}")

        if action == 'back_to_base':
            row_index, player_data = google_sheets.find_player_row(user_id)
            if player_data:
                base_text = content.get_base_panel_text(player_data)
                bot.edit_message_text(base_text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_main_menu_keyboard(is_inline=True))
        elif action.startswith('build_'):
            building_key = action.split('_')[1]
            handle_upgrade_request(bot, scheduler, user_id, building_key, call.message)
        # --- NEW: Handle clicks on the 'Train' buttons ---
        elif action.startswith('train_'):
            unit_key = action.split('_')[1]
            bot.edit_message_text("How many units would you like to train?", chat_id=call.message.chat.id, message_id=call.message.message_id)
            user_state[user_id] = partial(handle_train_quantity, bot, scheduler, unit_key)

        bot.answer_callback_query(call.id)

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
            send_build_menu(bot, message.from_user.id, message)
        # --- NEW: Handle Train Menu button press ---
        elif message.text == constants.MENU_TRAIN:
            send_train_menu(bot, message.from_user.id, message)
        else:
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
            bot.send_message(message.chat.id, f"The **{message.text}** system is not yet online.", reply_markup=markup, parse_mode='Markdown')

def handle_upgrade_request(bot, scheduler, user_id, building_key, message):
    # This function is mostly unchanged, but we pass `message` to edit it later.
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: bot.send_message(user_id, "Error: Player data not found."); return
    if player_data.get('build_queue_item_id'): bot.answer_callback_query(message.id, "Builder is busy."); return
    building_info = constants.BUILDING_DATA[building_key]
    level = int(player_data.get(building_info['id'], 0))
    cost = calculate_cost(building_info['base_cost'], building_info['cost_multiplier'], level + 1)
    for res, amount in cost.items():
        if int(player_data.get(res, 0)) < amount:
            bot.send_message(user_id, f"⚠️ Insufficient resources."); return
    construction_time = calculate_time(building_info['base_time_seconds'], building_info['time_multiplier'], level + 1)
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=construction_time)
    new_resources = {res: int(player_data.get(res, 0)) - amount for res, amount in cost.items()}
    db_updates = {**new_resources, 'build_queue_item_id': building_key, 'build_queue_finish_time': finish_time.isoformat()}
    if google_sheets.update_player_data(user_id, db_updates):
        scheduler.add_job(complete_upgrade_job, 'date', run_date=finish_time, args=[bot, user_id, building_key], id=f'upgrade_{user_id}_{time.time()}')
        bot.edit_message_text(f"✅ Upgrade started! Your **{building_info['name']}** will reach **Level {level + 1}** in {timedelta(seconds=construction_time)}.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML')
    else: bot.send_message(user_id, "⚠️ Error starting upgrade.")

def send_base_panel(bot, user_id, player_data):
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)

def send_build_menu(bot, user_id, message):
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
    text = "<b><u>⚒️ Construction Yard (Idle)</u></b>\nSelect a building to upgrade:\n"
    markup = InlineKeyboardMarkup(row_width=1)
    for key, info in constants.BUILDING_DATA.items():
        if int(player_data.get(info['id'], 0)) == 0 and key != 'barracks' and int(player_data.get('building_hq_level')) < 1: continue # Example prerequisite
        level = int(player_data.get(info['id'], 0))
        cost = calculate_cost(info['base_cost'], info['cost_multiplier'], level + 1)
        cost_str = " | ".join([f"{v:,} {constants.UNIT_DATA.get(k,{}).get('emoji','')} {k.capitalize()}" for k,v in cost.items()])
        text += f"\n{info['emoji']} <b>{info['name']}</b> (Level {level})"
        markup.add(InlineKeyboardButton(f"Upgrade - Cost: {cost_str}", callback_data=f"build_{key}"))
    markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

# --- NEW: Training Menu Logic ---
def send_train_menu(bot, user_id, message):
    """Displays the interactive training menu, checking prerequisites first."""
    row_index, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return

    # 1. Prerequisite Check: Barracks must exist.
    if int(player_data.get('building_barracks_level', 0)) < 1:
        bot.send_message(user_id, "A 🪖 **Barracks** is required to train units.\n\nConstruct one from the **'⚒️ Build'** menu first.", parse_mode="Markdown")
        return

    # 2. Queue Check: Is the trainer busy?
    if train_item_id := player_data.get('train_queue_item_id'):
        # In the next step, we'll show a countdown here. For now, just a message.
        text = f"<b><u>🪖 Barracks (Training)</u></b>\n\nYour barracks are busy training units. Please wait for completion."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
        bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)
        return
    
    # 3. Display Trainable Units
    text = f"<b><u>🪖 Barracks (Idle)</u></b>\nSelect a unit to train:\n"
    markup = InlineKeyboardMarkup(row_width=1)
    for key, info in constants.UNIT_DATA.items():
        if int(player_data.get('building_barracks_level', 0)) >= info['required_barracks_level']:
            cost_str = " | ".join([f"{v:,} {res.capitalize()}" for res, v in info['cost'].items()])
            text += f"\n{info['emoji']} <b>{info['name']}</b> (ATK:{info['stats']['attack']}/DEF:{info['stats']['defense']})"
            markup.add(InlineKeyboardButton(f"Train - {cost_str} / unit", callback_data=f"train_{key}"))

    markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

def handle_train_quantity(bot, scheduler, unit_key, message):
    """Handles the user's input for how many units to train."""
    user_id = message.from_user.id
    try:
        quantity = int(message.text)
        if quantity <= 0: raise ValueError
    except ValueError:
        bot.send_message(user_id, "Invalid quantity. Please enter a positive number.")
        user_state[user_id] = partial(handle_train_quantity, bot, scheduler, unit_key) # Re-ask
        return

    # Acknowledge and clear state. The full logic will be in the next step.
    unit_name = constants.UNIT_DATA[unit_key]['name']
    bot.send_message(user_id, f"Request to train {quantity}x {unit_name} acknowledged.\n\n"
                               f"The final step is to engineer the training scheduler. This will be our next operation.")
    if user_id in user_state: del user_state[user_id]
    
def get_main_menu_keyboard(is_inline=False):
    # This function is mostly unchanged
    if is_inline:
        markup = InlineKeyboardMarkup(row_width=3)
        buttons = [InlineKeyboardButton(b.text, callback_data=b.text) for b in [KeyboardButton(constants.MENU_BASE),...]]
    else:
        markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        buttons = [KeyboardButton(b) for b in [constants.MENU_BASE, constants.MENU_BUILD, constants.MENU_TRAIN, constants.MENU_RESEARCH, constants.MENU_ATTACK, constants.MENU_QUESTS, constants.MENU_SHOP, constants.MENU_PREMIUM, constants.MENU_MAP, constants.MENU_ALLIANCE]]
        markup.add(*buttons)
    return markup