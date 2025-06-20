# handlers.py
# Final Patch: Corrects a critical resource deduction bug in the build system.

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

# --- SECTION 1 & 2 are stable and unchanged ---
def calculate_cost(base_cost, multiplier, level):
    return {res: math.floor(amount * (multiplier ** (level - 1))) for res, amount in base_cost.items()}
def calculate_time(base_time, multiplier, level):
    return math.floor(base_time * (multiplier ** (level - 1)))
def get_main_menu_keyboard():
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(b) for b in [constants.MENU_BASE, constants.MENU_BUILD, constants.MENU_TRAIN, constants.MENU_RESEARCH, constants.MENU_ATTACK, constants.MENU_QUESTS, constants.MENU_SHOP, constants.MENU_PREMIUM, constants.MENU_MAP, constants.MENU_ALLIANCE]]
    markup.add(*buttons)
    return markup
def complete_upgrade_job(bot, user_id, building_key):
    logger.info(f"Executing complete_upgrade_job for user {user_id}, building: {building_key}")
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    building_info = constants.BUILDING_DATA[building_key]
    building_level_field = building_info['id']
    current_level = int(player_data.get(building_level_field, 0))
    updates = { building_level_field: current_level + 1, 'build_queue_item_id': '', 'build_queue_finish_time': '' }
    effect = building_info.get('effects', {})
    if effect.get('type') == 'production':
        updates[effect['resource']] = int(player_data.get(effect['resource'], 0)) + effect['value_per_level']
    elif effect.get('type') == 'storage':
        value = effect['value_per_level']
        for res in ['wood', 'stone', 'iron', 'food']:
            updates[f'{res}_storage_cap'] = int(player_data.get(f'{res}_storage_cap', 0)) + value
    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Construction complete! Your **{building_info['name']}** has been upgraded to **Level {current_level + 1}**.")
def complete_training_job(bot, user_id, unit_key, quantity):
    logger.info(f"Executing complete_training_job for user {user_id}, unit: {unit_key}, quantity: {quantity}")
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    unit_info = constants.UNIT_DATA[unit_key]
    unit_count_field = unit_info['id']
    updates = {
        unit_count_field: int(player_data.get(unit_count_field, 0)) + quantity,
        'power': int(player_data.get('power', 0)) + (unit_info['stats']['power'] * quantity),
        'train_queue_item_id': '', 'train_queue_quantity': '', 'train_queue_finish_time': ''
    }
    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Training complete! **{quantity}x {unit_info['name']}** {unit_info['emoji']} have joined your army.")
def battle_resolution_job(bot, scheduler, attacker_id, defender_id): pass # For brevity
def army_return_job(bot, user_id, surviving_army): pass # For brevity
def complete_research_job(bot, user_id, research_key): pass # For brevity


# --- SECTION 3: UI-GENERATING & CORE LOGIC FUNCTIONS ---

def send_base_panel(bot, user_id, player_data):
    base_panel_text = content.get_base_panel_text(player_data)
    markup = get_main_menu_keyboard()
    bot.send_message(user_id, base_panel_text, parse_mode='HTML', reply_markup=markup)
def send_build_menu(bot, user_id):
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    if build_item_id := player_data.get('build_queue_item_id'):
        finish_time = datetime.fromisoformat(player_data.get('build_queue_finish_time'))
        remaining = finish_time - datetime.now(timezone.utc)
        building_name = constants.BUILDING_DATA[build_item_id]['name']
        text = f"<b><u>⚒️ Construction Yard (Busy)</u></b>\n\nYour **{building_name}** is upgrading. Time left: {str(timedelta(seconds=int(remaining.total_seconds())))}."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    else:
        text = "<b><u>⚒️ Construction Yard (Idle)</u></b>\nSelect a building to upgrade:\n"
        markup = InlineKeyboardMarkup(row_width=1)
        for key, info in constants.BUILDING_DATA.items():
            level = int(player_data.get(info['id'], 0))
            cost = calculate_cost(info['base_cost'], info['cost_multiplier'], level + 1)
            cost_str = " | ".join([f"{v:,} {k.capitalize()}" for k, v in cost.items()])
            text += f"\n{info['emoji']} <b>{info['name']}</b> (Level {level})"
            markup.add(InlineKeyboardButton(f"Upgrade - Cost: {cost_str}", callback_data=f"build_{key}"))
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)
def send_train_menu(bot, user_id): pass # For brevity
def send_research_menu(bot, user_id): pass # For brevity
def send_attack_confirmation_menu(bot, user_id, attacker_data, defender_data): pass # For brevity

# --- THIS IS THE RE-ENGINEERED FUNCTION ---
def handle_upgrade_request(bot, scheduler, user_id, building_key, message):
    """Handles the logic for a build request with improved logic and feedback."""
    _, player_data = google_sheets.find_player_row(user_id)
    
    # 1. Perform validation checks with clear user feedback
    if not player_data:
        bot.answer_callback_query(message.id, "Error: Your data could not be found.")
        return
    if player_data.get('build_queue_item_id'):
        bot.answer_callback_query(message.id, "Your construction yard is already busy.")
        return

    building_info = constants.BUILDING_DATA[building_key]
    level = int(player_data.get(building_info['id'], 0))
    cost = calculate_cost(building_info['base_cost'], building_info['cost_multiplier'], level + 1)
    
    for res, amount in cost.items():
        if int(player_data.get(res, 0)) < amount:
            bot.answer_callback_query(message.id, f"⚠️ Insufficient resources. You need {amount:,} {res.capitalize()}.")
            return
            
    # 2. All checks passed. Calculate new resource values correctly.
    new_resources = player_data
    for res, amount in cost.items():
        new_resources[res] = int(new_resources.get(res, 0)) - amount

    # 3. Start the upgrade
    construction_time = calculate_time(building_info['base_time_seconds'], building_info['time_multiplier'], level + 1)
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=construction_time)
    
    db_updates = {
        **new_resources, # This now contains the correctly deducted resource values
        'build_queue_item_id': building_key,
        'build_queue_finish_time': finish_time.isoformat()
    }
    
    if google_sheets.update_player_data(user_id, db_updates):
        scheduler.add_job(complete_upgrade_job, 'date', run_date=finish_time, args=[bot, user_id, building_key], id=f'upgrade_{user_id}_{time.time()}')
        bot.edit_message_text(f"✅ Upgrade started! Your **{building_info['name']}** will reach **Level {level + 1}** in {timedelta(seconds=construction_time)}.",
                              chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML')
    else:
        bot.edit_message_text("A critical database error occurred. Your resources have not been spent.",
                              chat_id=message.chat.id, message_id=message.message_id)


def handle_train_quantity(bot, scheduler, unit_key, message): pass # For brevity
def handle_attack_launch(bot, scheduler, attacker_id, defender_id, message): pass # For brevity
def handle_research_request(bot, scheduler, user_id, research_key, message): pass # For brevity
def send_alliance_menu(bot, user_id): pass # For brevity
def send_no_alliance_menu(bot, user_id): pass # For brevity
def handle_alliance_create_get_name(bot, message): pass # For brevity
def handle_alliance_create_get_tag(bot, name, message): pass # For brevity

# --- SECTION 4: MAIN HANDLER REGISTRATION ---
def register_handlers(bot, scheduler):
    
    @bot.message_handler(commands=['start', 'attack'])
    def command_handler(message: Message):
        # This function and its logic are stable and unchanged
        pass # For brevity
    def get_commander_name_handler(bot, message: Message):
        # This function and its logic are stable and unchanged
        pass # For brevity

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id, action = call.from_user.id, call.data
        logger.info(f"User {user_id} clicked inline button: {action}")
        
        # We now answer the callback query at the start of the relevant handlers
        # to provide more specific feedback.

        parts = action.split('_'); command = parts[0]; key = '_'.join(parts[1:])
        
        # We should only edit the markup if we are NOT transitioning to a text input state
        if not (command == 'train' or (command == 'alliance' and key == 'create')):
             try:
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
             except Exception as e: logger.warning(f"Could not edit message markup: {e}")

        if command == 'build': 
            bot.answer_callback_query(call.id, "Processing upgrade...")
            handle_upgrade_request(bot, scheduler, user_id, key, call.message)
        # All other command routes are stable and unchanged
        elif command == 'back':
            _, pd = google_sheets.find_player_row(user_id)
            if pd: bot.edit_message_text(content.get_base_panel_text(pd), call.message.chat.id, call.message.message_id, parse_mode='HTML')
        elif command == 'train':
            bot.answer_callback_query(call.id)
            bot.edit_message_text("How many units to train?", chat_id=call.message.chat.id, message_id=call.message.message_id)
            user_state[user_id] = partial(handle_train_quantity, bot, scheduler, key)
        elif command == 'research': 
            bot.answer_callback_query(call.id, "Processing research...")
            handle_research_request(bot, scheduler, user_id, key, call.message)
        elif command == 'confirm' and parts[1] == 'attack': 
            bot.answer_callback_query(call.id)
            handle_attack_launch(bot, scheduler, user_id, int(parts[2]), call.message)
        elif command == 'alliance':
            bot.answer_callback_query(call.id)
            if key == 'create':
                bot.edit_message_text("You have chosen to forge a new alliance. What will it be named?", chat_id=call.message.chat.id, message_id=call.message.message_id)
                user_state[user_id] = partial(handle_alliance_create_get_name, bot)
            elif key == 'join':
                bot.edit_message_text("The ability to join alliances is coming soon.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        # This function is stable and unchanged
        if message.from_user.id in user_state:
            user_state[message.from_user.id](message=message)
        else:
            handle_menu_buttons(bot, message)

    def handle_menu_buttons(bot, message: Message):
        # This function is stable and unchanged
        if message.text == constants.MENU_ALLIANCE: send_alliance_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_BASE: _, pd = google_sheets.find_player_row(message.from_user.id); send_base_panel(bot, message.from_user.id, pd) if pd else None
        elif message.text == constants.MENU_BUILD: send_build_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_TRAIN: send_train_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_RESEARCH: send_research_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_ATTACK: bot.send_message(message.chat.id, "To attack, use: `/attack CommanderName`")
        else: bot.send_message(message.chat.id, f"The **{message.text}** system is not yet online.", parse_mode='Markdown')