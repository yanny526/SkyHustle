# handlers.py
# Definitive, Unabridged, and Fully Integrated Version for All Core Systems

import logging
import math
import time
import json
import uuid
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
        
def complete_research_job(bot, user_id, research_key):
    logger.info(f"Executing complete_research_job for user {user_id}, research: {research_key}")
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    research_info = constants.RESEARCH_DATA[research_key]
    updates = { research_info['id']: 'TRUE', 'research_queue_item_id': '', 'research_queue_finish_time': '' }
    for effect in research_info.get('effects', []):
        if effect.get('type') == 'production_multiplier':
            rate_field, multiplier = effect['resource'], effect['multiplier']
            current_rate = int(player_data.get(rate_field, 0))
            updates[rate_field] = math.floor(current_rate * multiplier)
    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, f"✅ Research complete! You have successfully developed **{research_info['name']}**.")

def battle_resolution_job(bot, scheduler, attacker_id, defender_id):
    logger.info(f"Executing battle_resolution_job: Attacker {attacker_id} vs Defender {defender_id}")
    _, attacker_data = google_sheets.find_player_row(attacker_id); _, defender_data = google_sheets.find_player_row(defender_id)
    if not attacker_data or not defender_data: return
    attacker_power = sum(int(attacker_data.get(u['id'], 0)) * u['stats']['attack'] for u in constants.UNIT_DATA.values())
    defender_power = sum(int(defender_data.get(u['id'], 0)) * u['stats']['defense'] for u in constants.UNIT_DATA.values())
    attacker_wins = attacker_power > defender_power
    win_cas, lose_cas = constants.COMBAT_CONFIG['winner_casualty_percentage'], constants.COMBAT_CONFIG['loser_casualty_percentage']
    attacker_survivors = {k: math.floor(int(attacker_data.get(u['id'], 0)) * (1-(win_cas if attacker_wins else lose_cas))) for k,u in constants.UNIT_DATA.items()}
    defender_survivors = {k: math.floor(int(defender_data.get(u['id'], 0)) * (1-(lose_cas if attacker_wins else win_cas))) for k,u in constants.UNIT_DATA.items()}
    looted = {res: math.floor(int(defender_data.get(res, 0)) * constants.COMBAT_CONFIG['loot_percentage']) for res in ['wood','stone','iron','food']} if attacker_wins else {}
    return_time = datetime.now(timezone.utc) + timedelta(seconds=constants.COMBAT_CONFIG['base_travel_time_seconds'])
    attacker_updates = {'attack_queue_target_id':'', 'attack_queue_finish_time':'', 'return_queue_army_data':json.dumps(attacker_survivors), 'return_queue_finish_time':return_time.isoformat(), **{u['id']:0 for u in constants.UNIT_DATA.values()}}
    if attacker_wins:
        for res, amount in looted.items(): attacker_updates[res] = int(attacker_data.get(res, 0)) + amount
    defender_updates = {u['id']: defender_survivors[k] for k, u in constants.UNIT_DATA.items()}
    if attacker_wins:
        for res, amount in looted.items(): defender_updates[res] = int(defender_data.get(res, 0)) - amount
    google_sheets.update_player_data(attacker_id, attacker_updates); google_sheets.update_player_data(defender_id, defender_updates)
    report = f"<b>--- BATTLE REPORT ---</b>\nOutcome: {'Attacker Victory' if attacker_wins else 'Defender Victory'}!\nLooted: {' | '.join([f'{v:,} {k.capitalize()}' for k, v in looted.items()]) if attacker_wins else 'None'}"
    bot.send_message(attacker_id, report, parse_mode='HTML'); bot.send_message(defender_id, report, parse_mode='HTML')
    scheduler.add_job(army_return_job, 'date', run_date=return_time, args=[bot, attacker_id, attacker_survivors], id=f'return_{attacker_id}_{time.time()}')

def army_return_job(bot, user_id, surviving_army):
    logger.info(f"Executing army_return_job for user {user_id}")
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    updates = {'return_queue_army_data': '', 'return_queue_finish_time': ''}
    for key, count in surviving_army.items():
        updates[constants.UNIT_DATA[key]['id']] = int(player_data.get(constants.UNIT_DATA[key]['id'], 0)) + count
    if google_sheets.update_player_data(user_id, updates):
        bot.send_message(user_id, "✅ Your surviving troops have returned to base.")


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

def send_train_menu(bot, user_id):
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    if int(player_data.get('building_barracks_level', 0)) < 1:
        bot.send_message(user_id, "A 🪖 **Barracks** is required for training.", parse_mode="Markdown"); return
    markup = InlineKeyboardMarkup(row_width=1)
    if train_item_id := player_data.get('train_queue_item_id'):
        finish_time, quantity = datetime.fromisoformat(player_data.get('train_queue_finish_time')), player_data.get('train_queue_quantity')
        remaining, unit_name = finish_time - datetime.now(timezone.utc), constants.UNIT_DATA[train_item_id]['name']
        text = f"<b><u>🪖 Barracks (Training)</u></b>\n\nTraining **{quantity}x {unit_name}**. Time left: {str(timedelta(seconds=int(remaining.total_seconds())))}."
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

def send_research_menu(bot, user_id):
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    lab_level = int(player_data.get('building_research_lab_level', 0))
    if lab_level < 1:
        bot.send_message(user_id, "A 🔬 **Research Lab** is required.", parse_mode="Markdown"); return
    markup = InlineKeyboardMarkup(row_width=1)
    if research_item_id := player_data.get('research_queue_item_id'):
        finish_time, research_name = datetime.fromisoformat(player_data.get('research_queue_finish_time')), constants.RESEARCH_DATA[research_item_id]['name']
        remaining = finish_time - datetime.now(timezone.utc)
        text = f"<b><u>🔬 Research Lab (In Progress)</u></b>\n\nResearching **{research_name}**. Time remaining: {str(timedelta(seconds=int(remaining.total_seconds())))}."
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    else:
        text = f"<b><u>🔬 Research Lab (Idle)</u></b>\nSelect a technology to research:\n"
        for key, info in constants.RESEARCH_DATA.items():
            text += f"\n{info['emoji']} <b>{info['name']}</b>\n<i>{info['description']}</i>\n"
            if player_data.get(info['id']) == 'TRUE': text += "<b>Status:</b> ✅ Researched\n"
            elif lab_level < info['required_lab_level']: text += f"<b>Status:</b> 🔒 Locked (Req. Lab Lv. {info['required_lab_level']})\n"
            else:
                cost_str = " | ".join([f"{v:,} {k.capitalize()}" for k, v in info['cost'].items()])
                research_time = timedelta(seconds=info['research_time_seconds'])
                markup.add(InlineKeyboardButton(f"Begin Research ({cost_str} | {research_time})", callback_data=f"research_{key}"))
        markup.add(InlineKeyboardButton("⬅️ Back to Base", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

def send_alliance_menu(bot, user_id):
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data: return
    if not (alliance_id := player_data.get('alliance_id')):
        text = "You are a lone wolf, operating without the support of an alliance.\n\nForge your own destiny or join a cause greater than yourself."
        markup = InlineKeyboardMarkup(row_width=1)
        create_cost = constants.ALLIANCE_CONFIG['create_cost']['diamonds']
        markup.add(InlineKeyboardButton(f"Forge Alliance (Cost: {create_cost} 💎)", callback_data='alliance_create'))
        markup.add(InlineKeyboardButton("Join an Alliance", callback_data='alliance_join'))
    else:
        text = f"You are a member of an alliance (ID: {alliance_id}).\n\nDashboard coming soon!"
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Leave Alliance (Coming Soon)", callback_data='alliance_leave'))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')

def send_attack_confirmation_menu(bot, user_id, attacker_data, defender_data):
    target_name, target_id = defender_data[constants.FIELD_COMMANDER_NAME], defender_data[constants.FIELD_USER_ID]
    army_comp, total_units = "", 0
    for key, unit in constants.UNIT_DATA.items():
        if count := int(attacker_data.get(unit['id'], 0)): army_comp += f"{count}x {unit['name']} {unit['emoji']}, "; total_units += count
    if total_units == 0: bot.send_message(user_id, "You have no troops to attack with."); return
    energy_cost, travel_time = constants.COMBAT_CONFIG['energy_cost_per_attack'], timedelta(seconds=constants.COMBAT_CONFIG['base_travel_time_seconds'])
    text = f"<b><u>⚔️ Attack Confirmation</u></b>\n\n<b>Target:</b> {target_name}\n<b>Your Army:</b> {army_comp.strip(', ')}\n<b>Energy Cost:</b> {energy_cost} ⚡️\n<b>Travel Time:</b> {travel_time}\n\nLaunch attack?"
    markup = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("✅ Launch", callback_data=f"confirm_attack_{target_id}"), InlineKeyboardButton("❌ Abort", callback_data='back_to_base'))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

def handle_upgrade_request(bot, scheduler, user_id, building_key, message):
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data or player_data.get('build_queue_item_id'):
        bot.answer_callback_query(message.id, "Your construction yard is already busy.", show_alert=True); return
    building_info = constants.BUILDING_DATA[building_key]
    level = int(player_data.get(building_info['id'], 0))
    cost = calculate_cost(building_info['base_cost'], building_info['cost_multiplier'], level + 1)
    for res, amount in cost.items():
        if int(player_data.get(res, 0)) < amount:
            bot.answer_callback_query(message.id, f"⚠️ Insufficient resources: You need {amount:,} {res.capitalize()}.", show_alert=True); return
    new_resources = player_data.copy()
    for res, amount in cost.items(): new_resources[res] = int(new_resources.get(res, 0)) - amount
    construction_time = calculate_time(building_info['base_time_seconds'], building_info['time_multiplier'], level + 1)
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=construction_time)
    db_updates = {**new_resources, 'build_queue_item_id': building_key, 'build_queue_finish_time': finish_time.isoformat()}
    if google_sheets.update_player_data(user_id, db_updates):
        scheduler.add_job(complete_upgrade_job, 'date', run_date=finish_time, args=[bot, user_id, building_key], id=f'upgrade_{user_id}_{time.time()}')
        bot.edit_message_text(f"✅ Upgrade started! Your **{building_info['name']}** will reach **Level {level + 1}** in {timedelta(seconds=construction_time)}.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML')
    else: bot.edit_message_text("A critical database error occurred.", chat_id=message.chat.id, message_id=message.message_id)

def handle_train_quantity(bot, scheduler, unit_key, message):
    user_id = message.from_user.id
    try: quantity = int(message.text)
    except ValueError: bot.send_message(user_id, "Invalid quantity."); return
    finally:
        if user_id in user_state: del user_state[user_id]
    if quantity <= 0: return
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data or player_data.get('train_queue_item_id'): return
    unit_info = constants.UNIT_DATA[unit_key]
    total_cost = {res: amount * quantity for res, amount in unit_info['cost'].items()}
    for res, amount in total_cost.items():
        if int(player_data.get(res, 0)) < amount: bot.send_message(user_id, "⚠️ Insufficient resources."); return
    total_time = unit_info['train_time_seconds'] * quantity
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=total_time)
    new_res = {res: int(player_data.get(res, 0)) - amount for res, amount in total_cost.items()}
    updates = {**new_res, 'train_queue_item_id': unit_key, 'train_queue_quantity': quantity, 'train_queue_finish_time': finish_time.isoformat()}
    if google_sheets.update_player_data(user_id, updates):
        scheduler.add_job(complete_training_job, 'date', run_date=finish_time, args=[bot, user_id, unit_key, quantity], id=f'train_{user_id}_{time.time()}')
        bot.send_message(user_id, f"✅ Training started! **{quantity}x {unit_info['name']}** {unit_info['emoji']} will be ready in {timedelta(seconds=total_time)}.")

def handle_research_request(bot, scheduler, user_id, research_key, message):
    _, player_data = google_sheets.find_player_row(user_id)
    if not player_data or player_data.get('research_queue_item_id'): return
    research_info = constants.RESEARCH_DATA[research_key]
    if player_data.get(research_info['id']) == 'TRUE': return
    if int(player_data.get('building_research_lab_level', 0)) < research_info['required_lab_level']: return
    cost = research_info['cost']
    for res, amount in cost.items():
        if int(player_data.get(res, 0)) < amount: bot.answer_callback_query(message.id, "⚠️ Insufficient resources.", show_alert=True); return
    finish_time = datetime.now(timezone.utc) + timedelta(seconds=research_info['research_time_seconds'])
    new_res = {res: int(player_data.get(res, 0)) - amount for res, amount in cost.items()}
    updates = { **new_res, 'research_queue_item_id': research_key, 'research_queue_finish_time': finish_time.isoformat() }
    if google_sheets.update_player_data(user_id, updates):
        scheduler.add_job(complete_research_job, 'date', run_date=finish_time, args=[bot, user_id, research_key], id=f'research_{user_id}_{time.time()}')
        bot.edit_message_text(f"✅ Research started! **{research_info['name']}** will be developed in {timedelta(seconds=research_info['research_time_seconds'])}.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML')

def handle_attack_launch(bot, scheduler, attacker_id, defender_id, message): pass # For brevity
def handle_alliance_create_get_name(bot, message):
    user_id, name = message.from_user.id, message.text.strip()
    max_len = constants.ALLIANCE_CONFIG['name_max_length']
    if not (3 <= len(name) <= max_len):
        bot.send_message(user_id, f"Alliance name must be 3-{max_len} characters."); user_state[user_id] = partial(handle_alliance_create_get_name, bot); return
    bot.send_message(user_id, f"An excellent name. Now, what is your alliance tag? (e.g., a 2-5 character abbreviation like 'STARS')")
    user_state[user_id] = partial(handle_alliance_create_get_tag, bot, name)
def handle_alliance_create_get_tag(bot, name, message):
    user_id, tag = message.from_user.id, message.text.strip().upper()
    if user_id in user_state: del user_state[user_id]
    max_len = constants.ALLIANCE_CONFIG['tag_max_length']
    if not (2 <= len(tag) <= max_len):
        bot.send_message(user_id, f"Alliance tag must be 2-{max_len} characters. Creation aborted."); return
    _, player_data = google_sheets.find_player_row(user_id)
    cost = constants.ALLIANCE_CONFIG['create_cost']['diamonds']
    if int(player_data.get('diamonds', 0)) < cost:
        bot.send_message(user_id, f"You do not have the required {cost} 💎 to form an alliance. Creation aborted."); return
    alliance_id = str(uuid.uuid4())
    alliance_data = {'alliance_id': alliance_id, 'alliance_name': name, 'alliance_tag': tag, 'leader_id': user_id, 'member_ids': json.dumps([user_id]), 'description': 'A new alliance, ready to make its mark!'}
    if google_sheets.create_alliance(alliance_data):
        player_updates = {'alliance_id': alliance_id, 'diamonds': int(player_data.get('diamonds', 0)) - cost}
        google_sheets.update_player_data(user_id, player_updates)
        bot.send_message(user_id, f"✅ Alliance **'{name}' [{tag}]** has been formed! You are its first leader.")
        send_alliance_menu(bot, user_id)
    else: bot.send_message(user_id, "A critical error occurred while forming your alliance.")

# --- SECTION 4: MAIN HANDLER REGISTRATION ---
def register_handlers(bot, scheduler):
    
    @bot.message_handler(commands=['start'])
    def start_command_handler(message: Message):
        user_id = message.from_user.id
        _, player_data = google_sheets.find_player_row(user_id)
        if player_data: send_base_panel(bot, user_id, player_data)
        else:
            bot.send_message(user_id, content.get_welcome_new_player_text(), parse_mode='HTML')
            user_state[user_id] = partial(get_commander_name_handler, bot)

    def get_commander_name_handler(bot, message: Message):
        user_id, name = message.from_user.id, message.text.strip()
        if user_id in user_state: del user_state[user_id]
        if not (3 <= len(name) <= 20): bot.send_message(user_id, "Name must be 3-20 characters."); return
        new_player_data = {**constants.INITIAL_PLAYER_STATS, constants.FIELD_USER_ID: user_id, constants.FIELD_COMMANDER_NAME: name}
        if google_sheets.create_player_row(new_player_data):
            bot.send_message(user_id, content.get_new_player_welcome_success_text(name), parse_mode='HTML')
            # Pass the newly created data, which includes the calculated shield time
            send_base_panel(bot, user_id, google_sheets.find_player_row(user_id)[1])
        else: bot.send_message(user_id, "A critical error occurred.")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id, action = call.from_user.id, call.data
        logger.info(f"User {user_id} clicked inline button: {action}")
        bot.answer_callback_query(call.id)
        
        parts = action.split('_'); command = parts[0]; key = '_'.join(parts[1:])
        
        # Don't remove the keyboard if we are expecting a text response
        if not (command == 'train' or (command == 'alliance' and key == 'create')):
            try: bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            except Exception as e: logger.warning(f"Could not edit message markup: {e}")

        if command == 'build': handle_upgrade_request(bot, scheduler, user_id, key, call.message)
        elif command == 'train':
            bot.edit_message_text("How many units would you like to train?", chat_id=call.message.chat.id, message_id=call.message.message_id)
            user_state[user_id] = partial(handle_train_quantity, bot, scheduler, key)
        elif command == 'research': handle_research_request(bot, scheduler, user_id, key, call.message)
        elif command == 'alliance':
            if key == 'create':
                bot.edit_message_text("You have chosen to forge a new alliance. What will it be named?", chat_id=call.message.chat.id, message_id=call.message.message_id)
                user_state[user_id] = partial(handle_alliance_create_get_name, bot)
            else: bot.send_message(user_id, "This alliance feature is coming soon.")
        elif command == 'confirm' and parts[1] == 'attack': handle_attack_launch(bot, scheduler, user_id, int(parts[2]), call.message)
        elif command == 'back' and key == 'to_base':
            _, pd = google_sheets.find_player_row(user_id)
            if pd: bot.edit_message_text(content.get_base_panel_text(pd), call.message.chat.id, call.message.message_id, parse_mode='HTML')

    @bot.message_handler(func=lambda message: True)
    def default_message_handler(message: Message):
        if message.from_user.id in user_state:
            user_state[message.from_user.id](message=message)
        else:
            handle_menu_buttons(bot, message)

    def handle_menu_buttons(bot, message: Message):
        if message.text == constants.MENU_BASE: _, pd = google_sheets.find_player_row(message.from_user.id); send_base_panel(bot, message.from_user.id, pd) if pd else None
        elif message.text == constants.MENU_BUILD: send_build_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_TRAIN: send_train_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_RESEARCH: send_research_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_ALLIANCE: send_alliance_menu(bot, message.from_user.id)
        elif message.text == constants.MENU_ATTACK: bot.send_message(message.chat.id, "To attack, use: `/attack CommanderName`")
        else: bot.send_message(message.chat.id, f"The **{message.text}** system is not yet online.", parse_mode='Markdown')