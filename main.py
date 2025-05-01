# main.py — SkyHustle Unified Version (Part 1 of X)
import os
import json
import time
import base64
import random
import logging
import datetime
# ── Load Environment Credentials ────────────────────────────────
BASE64_CREDS = os.environ.get("BASE64_CREDS")
print("ENV:", os.environ)
print("BASE64_CREDS:", BASE64_CREDS)
if not BASE64_CREDS:
    raise ValueError("❌ Environment variable BASE64_CREDS is missing.")

creds_json = json.loads(base64.b64decode(BASE64_CREDS.strip()).decode())

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Environment Variables ───────────────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
SHEET_KEY = os.getenv("SHEET_KEY")
BASE64_CREDS = os.environ.get("BASE64_CREDS")
# ── Google Sheets Setup ─────────────────────────────────────────
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
if not BASE64_CREDS:
    raise ValueError("❌ Environment variable BASE64_CREDS is missing for Google Sheets.")
creds_json = json.loads(base64.b64decode(BASE64_CREDS.strip()).decode())
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
sheet = gspread.authorize(creds).open_by_key(SHEET_KEY)


# ── Utility: Get Player Name by ID ──────────────────────────────
def get_player_name(user_id: str):
    try:
        row = players_sheet.find(user_id).row
        return players_sheet.cell(row, 2).value or user_id
    except:
        return user_id

# ── Utility: Get or Create Worksheet ────────────────────────────
def get_or_create_worksheet(sheet, title, headers):
    try:
        ws = sheet.worksheet(title)
    except:
        ws = sheet.add_worksheet(title=title, rows="1000", cols=str(len(headers)))
        ws.append_row(headers)
    return ws

# ── Core Worksheets ─────────────────────────────────────────────
resources_sheet = get_or_create_worksheet(sheet, "Resources", ["ID", "gold", "iron", "tech", "crystals"])
players_sheet = get_or_create_worksheet(sheet, "Players", ["ID", "name", "faction"])
buildings_sheet = get_or_create_worksheet(sheet, "Buildings", ["ID", "mine", "barracks", "lab"])
army_sheet = get_or_create_worksheet(sheet, "Army", ["ID", "infantry", "sniper", "tank"])
research_sheet = get_or_create_worksheet(sheet, "Research", ["ID", "power", "production"])
zones_sheet = get_or_create_worksheet(sheet, "Zones", ["zone", "owner_id"])
mission_sheet = get_or_create_worksheet(sheet, "Missions", ["ID", "build", "train", "attack", "capture"])
base_sheet = get_or_create_worksheet(sheet, "Bases", ["ID", "base_level"])
daily_sheet = get_or_create_worksheet(sheet, "Daily", ["ID", "last_claim"])
boss_sheet = get_or_create_worksheet(sheet, "RaidBoss", ["boss_name", "hp"])
inbox_sheet = get_or_create_worksheet(sheet, "Inbox", ["ID", "message"])
event_sheet = get_or_create_worksheet(sheet, "Events", ["name", "description", "active"])
rank_sheet = get_or_create_worksheet(sheet, "Ranks", ["ID", "score"])
faction_sheet = get_or_create_worksheet(sheet, "Factions", ["Faction", "Points"])
trade_sheet = get_or_create_worksheet(sheet, "Trades", ["From", "To", "Resource", "Amount"])
# main.py — SkyHustle Unified Version (Part 2 of X)
# ── Player Registration ─────────────────────────────────────────
def register_player(user_id: int, username: str):
    try:
        players_sheet.find(str(user_id))
    except:
        players_sheet.append_row([str(user_id), username or "Unknown", "none"])
        resources_sheet.append_row([str(user_id), "500", "300", "0", "0"])
        buildings_sheet.append_row([str(user_id), "1", "1", "1"])
        army_sheet.append_row([str(user_id), "0", "0", "0"])
        research_sheet.append_row([str(user_id), "0", "0"])
        mission_sheet.append_row([str(user_id), "0", "0", "0", "0"])
        base_sheet.append_row([str(user_id), "1"])
        daily_sheet.append_row([str(user_id), "2000-01-01"])
        rank_sheet.append_row([str(user_id), "0"])

# ── /start Command ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_player(user.id, user.username)

    keyboard = [[InlineKeyboardButton("Enter SkyHustle 🌌", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Welcome Commander *{user.first_name}*

Your empire begins now. 🌍
Tap below to enter command mode.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

# ── Main Menu Callback ──────────────────────────────────────────
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🏗 Build", callback_data="build_menu"),
         InlineKeyboardButton("🧑‍✈️ Train", callback_data="train_menu")],
        [InlineKeyboardButton("⚔️ Attack", callback_data="attack_menu"),
         InlineKeyboardButton("🧪 Research", callback_data="research_menu")],
        [InlineKeyboardButton("🏙 Zones", callback_data="zone_menu"),
         InlineKeyboardButton("🛒 Store", callback_data="store_menu")],
        [InlineKeyboardButton("🎯 Missions", callback_data="mission_menu"),
         InlineKeyboardButton("📬 Inbox", callback_data="inbox_menu")],
        [InlineKeyboardButton("💼 Faction", callback_data="faction_menu"),
         InlineKeyboardButton("🌐 Events", callback_data="event_menu")],
        [InlineKeyboardButton("🗺 Base", callback_data="base_menu"),
         InlineKeyboardButton("👑 Leaderboard", callback_data="rank_menu")],
    ]
    await query.edit_message_text(
        "📟 *Command Panel*\nChoose your next action:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# main.py — SkyHustle Unified Version (Part 3 of X)
# ── Building Upgrade Logic ──────────────────────────────────────
def upgrade_building(user_id: int, building: str):
    col_map = {"mine": 2, "barracks": 3, "lab": 4}
    if building not in col_map:
        return False, "Invalid building."

    row = buildings_sheet.find(str(user_id)).row
    current_level = int(buildings_sheet.cell(row, col_map[building]).value)
    cost = current_level * 100

    res_row = resources_sheet.find(str(user_id)).row
    gold = int(resources_sheet.cell(res_row, 2).value)
    if gold < cost:
        return False, "Not enough gold."

    resources_sheet.update_cell(res_row, 2, gold - cost)
    buildings_sheet.update_cell(row, col_map[building], current_level + 1)

    mark_mission(user_id, "build")
    update_score(user_id, 10)

    return True, f"{building.capitalize()} upgraded to level {current_level + 1}!"

# ── Build Menu ──────────────────────────────────────────────────
async def build_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Upgrade Mine", callback_data="build_mine")],
        [InlineKeyboardButton("Upgrade Barracks", callback_data="build_barracks")],
        [InlineKeyboardButton("Upgrade Lab", callback_data="build_lab")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(
        "🏗 *Choose a building to upgrade:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Build Action Handler ────────────────────────────────────────
async def handle_build_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    building = query.data.replace("build_", "")
    success, msg = upgrade_building(user_id, building)
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="build_menu")]]
    await query.edit_message_text(
        f"🏗 {msg}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# main.py — SkyHustle Unified Version (Part 4 of X)
# ── Training Logic ──────────────────────────────────────────────
def train_unit(user_id: int, unit: str):
    costs = {"infantry": 50, "sniper": 100, "tank": 200}
    col_map = {"infantry": 2, "sniper": 3, "tank": 4}

    if unit not in costs:
        return False, "Invalid unit."

    res_row = resources_sheet.find(str(user_id)).row
    gold = int(resources_sheet.cell(res_row, 2).value)
    if gold < costs[unit]:
        return False, "Not enough gold."

    army_row = army_sheet.find(str(user_id)).row
    current = int(army_sheet.cell(army_row, col_map[unit]).value)

    resources_sheet.update_cell(res_row, 2, gold - costs[unit])
    army_sheet.update_cell(army_row, col_map[unit], current + 1)

    mark_mission(user_id, "train")
    update_score(user_id, 5)

    return True, f"Trained 1 {unit.capitalize()} successfully."

# ── Train Menu ──────────────────────────────────────────────────
async def train_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Train Infantry (50g)", callback_data="train_infantry")],
        [InlineKeyboardButton("Train Sniper (100g)", callback_data="train_sniper")],
        [InlineKeyboardButton("Train Tank (200g)", callback_data="train_tank")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(
        "🧑‍✈️ *Choose a unit to train:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Train Action Handler ────────────────────────────────────────
async def handle_train_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    unit = query.data.replace("train_", "")
    success, msg = train_unit(user_id, unit)
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="train_menu")]]
    await query.edit_message_text(
        f"🧑‍✈️ {msg}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# main.py — SkyHustle Unified Version (Part 5 of X)
# ── Combat Power Calculation ────────────────────────────────────
def get_combat_power(user_id: int):
    try:
        row = army_sheet.find(str(user_id)).row
        infantry = int(army_sheet.cell(row, 2).value)
        sniper = int(army_sheet.cell(row, 3).value)
        tank = int(army_sheet.cell(row, 4).value)
        return infantry * 1 + sniper * 3 + tank * 5
    except:
        return 0

# ── Attack Menu ─────────────────────────────────────────────────
async def attack_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⚔️ Send /attack <user_id> to initiate battle.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]])
    )

# ── /attack Command ─────────────────────────────────────────────
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attacker_id = update.effective_user.id
    if not context.args:
        return await update.message.reply_text("Usage: /attack <user_id>")

    try:
        target_id = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ Invalid ID format.")

    attacker_power = get_combat_power(attacker_id)
    defender_power = get_combat_power(target_id)

    if attacker_power == 0:
        return await update.message.reply_text("⚠️ You have no troops to send.")

    if defender_power == 0:
        result = "Victory! 🏆 Enemy had no defense."
        mark_mission(attacker_id, "attack")
        update_score(attacker_id, 20)
    elif attacker_power > defender_power:
        result = "Victory! 🏆 You overpowered the enemy."
        mark_mission(attacker_id, "attack")
        update_score(attacker_id, 20)
    elif attacker_power == defender_power:
        result = "Draw ⚔️ Equal strength."
    else:
        result = "Defeat! 💀 The enemy was stronger."

    await update.message.reply_text(
        f"⚔️ Combat Result:\nYou: {attacker_power} vs Enemy: {defender_power}\n\n{result}",
        parse_mode=ParseMode.MARKDOWN
    )
# main.py — SkyHustle Unified Version (Part 6 of X)
# ── /research Command ───────────────────────────────────────────
async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        row = research_sheet.find(str(user_id)).row
    except:
        research_sheet.append_row([str(user_id), "0", "0"])
        row = research_sheet.find(str(user_id)).row

    power = int(research_sheet.cell(row, 2).value)
    prod = int(research_sheet.cell(row, 3).value)
    new_power = power + 1
    new_prod = prod + 1

    research_sheet.update_cell(row, 2, new_power)
    research_sheet.update_cell(row, 3, new_prod)

    await update.message.reply_text(
        f"🔬 Research complete!\n+1 Power Bonus, +1 Production Bonus\n\n"
        f"Current Power: {new_power}\nCurrent Production: {new_prod}",
        parse_mode=ParseMode.MARKDOWN
    )

# ── Passive Resource Generation ─────────────────────────────────
def generate_resources():
    all_ids = [cell.value for cell in resources_sheet.col_values(1)[1:]]
    for user_id in all_ids:
        try:
            row = resources_sheet.find(user_id).row
            prod_row = research_sheet.find(user_id).row
            prod_bonus = int(research_sheet.cell(prod_row, 3).value)

            gold = int(resources_sheet.cell(row, 2).value)
            iron = int(resources_sheet.cell(row, 3).value)
            tech = int(resources_sheet.cell(row, 4).value)

            resources_sheet.update_cell(row, 2, gold + 10 + prod_bonus)
            resources_sheet.update_cell(row, 3, iron + 5 + prod_bonus)
            resources_sheet.update_cell(row, 4, tech + 2 + prod_bonus)
        except Exception as e:
            logger.warning(f"Failed to update resources for {user_id}: {e}")

# ── /collect Command ────────────────────────────────────────────
async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    generate_resources()
    await update.message.reply_text("💰 Resources generated for all users.")
# main.py — SkyHustle Unified Version (Part 7 of X)
# ── Zone List ───────────────────────────────────────────────────
ZONE_LIST = ["Alpha", "Bravo", "Charlie", "Delta"]

# ── Capture Zone Utility ────────────────────────────────────────
def capture_zone(zone: str, user_id: int):
    try:
        cell = zones_sheet.find(zone)
        zones_sheet.update_cell(cell.row, 2, str(user_id))
    except:
        zones_sheet.append_row([zone, str(user_id)])
    mark_mission(user_id, "capture")
    update_score(user_id, 15)

# ── /zones Command ──────────────────────────────────────────────
async def zones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🌍 *Zone Control Overview*\n\n"
    for zone in ZONE_LIST:
        try:
            cell = zones_sheet.find(zone)
            owner_id = zones_sheet.cell(cell.row, 2).value
            message += f"▪️ {zone}: Controlled by `{owner_id}`\n"
        except:
            message += f"▪️ {zone}: _Unclaimed_\n"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

# ── /capture Command ────────────────────────────────────────────
async def capture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        return await update.message.reply_text("Usage: /capture <zone_name>")

    zone = context.args[0].capitalize()
    if zone not in ZONE_LIST:
        return await update.message.reply_text("❌ Invalid zone.")

    capture_zone(zone, user_id)
    await update.message.reply_text(f"✅ You have claimed zone *{zone}*.", parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 8 of X)
# ── Missions Setup ──────────────────────────────────────────────
MISSIONS = {
    "build": {"desc": "Upgrade any building", "reward": 100},
    "train": {"desc": "Train any unit", "reward": 80},
    "attack": {"desc": "Win a battle", "reward": 120},
    "capture": {"desc": "Claim a zone", "reward": 90},
}

# ── Ensure Mission Row Exists ───────────────────────────────────
def ensure_mission_row(user_id):
    try:
        mission_sheet.find(str(user_id))
    except:
        mission_sheet.append_row([str(user_id), "0", "0", "0", "0"])

# ── Mark Mission Complete ───────────────────────────────────────
def mark_mission(user_id, mission_key):
    ensure_mission_row(user_id)
    row = mission_sheet.find(str(user_id)).row
    col = list(MISSIONS.keys()).index(mission_key) + 2
    mission_sheet.update_cell(row, col, "1")

# ── /missions Command ───────────────────────────────────────────
async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_mission_row(user_id)
    row = mission_sheet.find(str(user_id)).row
    msg = "📋 *Mission Progress:*\n"
    for idx, key in enumerate(MISSIONS):
        status = mission_sheet.cell(row, idx + 2).value
        check = "✅" if status == "1" else "⬜"
        msg += f"{check} {MISSIONS[key]['desc']}\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# ── /claim Command ──────────────────────────────────────────────
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_mission_row(user_id)
    row = mission_sheet.find(str(user_id)).row
    res_row = resources_sheet.find(str(user_id)).row
    total = 0

    for idx, key in enumerate(MISSIONS):
        completed = mission_sheet.cell(row, idx + 2).value
        if completed == "1":
            total += MISSIONS[key]['reward']
            mission_sheet.update_cell(row, idx + 2, "0")

    if total > 0:
        current_gold = int(resources_sheet.cell(res_row, 2).value)
        resources_sheet.update_cell(res_row, 2, current_gold + total)
        await update.message.reply_text(f"🎉 Claimed {total} gold from completed missions!", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ No missions completed.", parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 9 of X)
# ── Faction Setup ───────────────────────────────────────────────
FACTIONS = {
    "faction_tech": "Techlords",
    "faction_guard": "Guardians",
    "faction_war": "Warlords",
}

# ── /faction Command ────────────────────────────────────────────
async def faction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚙️ Techlords", callback_data="faction_tech")],
        [InlineKeyboardButton("🛡 Guardians", callback_data="faction_guard")],
        [InlineKeyboardButton("💣 Warlords", callback_data="faction_war")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await update.message.reply_text(
        "🏳 Choose your Faction:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Handle Faction Selection ────────────────────────────────────
async def handle_faction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chosen = FACTIONS.get(query.data)

    if not chosen:
        return await query.edit_message_text("❌ Invalid faction.")

    row = players_sheet.find(str(user_id)).row
    players_sheet.update_cell(row, 3, chosen)
    await query.edit_message_text(f"✅ You joined the *{chosen}* faction!", parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 10 of X)
# ── Ensure Base Row ─────────────────────────────────────────────
def ensure_base_row(user_id):
    try:
        base_sheet.find(str(user_id))
    except:
        base_sheet.append_row([str(user_id), "1"])

# ── /base Command ───────────────────────────────────────────────
async def base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_base_row(user_id)
    row = base_sheet.find(str(user_id)).row
    level = int(base_sheet.cell(row, 2).value)
    await update.message.reply_text(f"🏗 Your base is currently at level {level}.")

# ── /expand Command ─────────────────────────────────────────────
async def expand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_base_row(user_id)
    row = base_sheet.find(str(user_id)).row
    res_row = resources_sheet.find(str(user_id)).row

    level = int(base_sheet.cell(row, 2).value)
    gold = int(resources_sheet.cell(res_row, 2).value)
    cost = 200 * level

    if gold < cost:
        return await update.message.reply_text("❌ Not enough gold to expand base.")

    resources_sheet.update_cell(res_row, 2, gold - cost)
    base_sheet.update_cell(row, 2, level + 1)
    update_score(user_id, 15)

    await update.message.reply_text(f"🎉 Base expanded to level {level + 1}! Cost: {cost} gold.")
# main.py — SkyHustle Unified Version (Part 11 of X)
# ── /daily Command ──────────────────────────────────────────────
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today = datetime.datetime.utcnow().date()

    try:
        cell = daily_sheet.find(user_id)
        row = cell.row
        last_claim_str = daily_sheet.cell(row, 2).value
        last_claim = datetime.datetime.strptime(last_claim_str, "%Y-%m-%d").date()

        if last_claim == today:
            return await update.message.reply_text("🕐 You've already claimed today's reward.")

        daily_sheet.update_cell(row, 2, today.isoformat())
    except:
        daily_sheet.append_row([user_id, today.isoformat()])

    res_row = resources_sheet.find(user_id).row
    current_gold = int(resources_sheet.cell(res_row, 2).value)
    bonus = 150

    resources_sheet.update_cell(res_row, 2, current_gold + bonus)
    update_score(user_id, 10)

    await update.message.reply_text(f"🎁 You received your daily reward: {bonus} gold! Come back tomorrow.")
# main.py — SkyHustle Unified Version (Part 12 of X)
# ── Black Market Item Config ───────────────────────────────────
BLACK_MARKET_ITEMS = {
    "revive": {"name": "Revive Boost", "desc": "Revive all troops.", "cost": 500},
    "shield": {"name": "Shield Generator", "desc": "Block next attack.", "cost": 400},
    "emp": {"name": "EMP Device", "desc": "Weaken enemy defenses.", "cost": 300},
}

# ── /blackmarket Command ────────────────────────────────────────
async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for key, item in BLACK_MARKET_ITEMS.items():
        btn_text = f"{item['name']} - {item['cost']}g"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"bm_{key}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])

    await update.message.reply_text(
        "🛒 *Black Market Items:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Handle Black Market Purchase ────────────────────────────────
async def handle_blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    item_key = query.data.replace("bm_", "")
    item = BLACK_MARKET_ITEMS.get(item_key)

    if not item:
        return await query.edit_message_text("❌ Invalid item.")

    row = resources_sheet.find(str(user_id)).row
    gold = int(resources_sheet.cell(row, 2).value)

    if gold < item['cost']:
        return await query.edit_message_text("❌ Not enough gold.")

    resources_sheet.update_cell(row, 2, gold - item['cost'])
    update_score(user_id, 10)

    await query.edit_message_text(
        f"✅ You bought *{item['name']}*\n_{item['desc']}_",
        parse_mode=ParseMode.MARKDOWN
    )
# main.py — SkyHustle Unified Version (Part 13 of X)
# ── Inbox Utility ───────────────────────────────────────────────
def send_inbox(user_id: str, message: str):
    inbox_sheet.append_row([user_id, message])

# ── /inbox Command ──────────────────────────────────────────────
async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    rows = inbox_sheet.get_all_records()
    messages = [row["message"] for row in rows if row["ID"] == user_id]

    if not messages:
        return await update.message.reply_text("📭 Your inbox is empty.")

    text = "📬 *Inbox Messages:*\n\n" + "\n".join(f"▪️ {msg}" for msg in messages[-10:])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 14 of X)
# ── PvE Boss Setup ──────────────────────────────────────────────
boss_data = {"Titan": 5000, "Overlord": 8000}

# ── /raid Command ───────────────────────────────────────────────
async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🛡 *Available PvE Raids:*\n\n"
    for name, hp in boss_data.items():
        try:
            row = boss_sheet.find(name).row
            current = int(boss_sheet.cell(row, 2).value)
        except:
            boss_sheet.append_row([name, str(hp)])
            current = hp
        msg += f"▪️ {name} - {current} HP\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# ── /fight Command ──────────────────────────────────────────────
async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /fight <boss_name>")

    boss_name = context.args[0].capitalize()
    if boss_name not in boss_data:
        return await update.message.reply_text("❌ Invalid boss.")

    user_id = update.effective_user.id
    power = get_combat_power(user_id)

    if power == 0:
        return await update.message.reply_text("⚠️ You have no units to attack with.")

    try:
        row = boss_sheet.find(boss_name).row
        hp = int(boss_sheet.cell(row, 2).value)
    except:
        row = boss_sheet.append_row([boss_name, str(boss_data[boss_name])]).row
        hp = boss_data[boss_name]

    new_hp = max(0, hp - power)
    boss_sheet.update_cell(row, 2, new_hp)
    result = "🩸 Survived" if new_hp > 0 else "☠️ Defeated"

    reward = 100 if new_hp == 0 else 30
    res_row = resources_sheet.find(str(user_id)).row
    current_gold = int(resources_sheet.cell(res_row, 2).value)
    resources_sheet.update_cell(res_row, 2, current_gold + reward)

    log_msg = f"You fought {boss_name}, dealt {power} damage. Result: {result}. +{reward} gold."
    send_inbox(str(user_id), log_msg)
    update_score(user_id, reward)

    await update.message.reply_text(
        f"⚔️ You attacked *{boss_name}* dealing *{power}* damage!\n"
        f"Current HP: {new_hp}\nResult: {result}\nReward: +{reward} gold",
        parse_mode=ParseMode.MARKDOWN
    )
# main.py — SkyHustle Unified Version (Part 15 of X)
# ── World Event Definitions ─────────────────────────────────────
events = [
    {"name": "Radiation Storm", "desc": "Mining yields halved for 1h"},
    {"name": "Meteor Shower", "desc": "+50% PvE gold for 30 min"},
    {"name": "War Cry", "desc": "Unit power doubled for 15 min"},
]

# ── /event Command ──────────────────────────────────────────────
async def event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🌐 *Active World Events:*\n\n"
    rows = event_sheet.get_all_records()
    active = [row for row in rows if row['active'] == '1']

    if not active:
        msg += "No events currently active."
    else:
        for e in active:
            msg += f"▪️ *{e['name']}* — _{e['description']}_\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# ── /trigger_event Command ──────────────────────────────────────
async def trigger_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /trigger_event <event_name>")

    name = " ".join(context.args).title()
    found = next((e for e in events if e["name"] == name), None)

    if not found:
        return await update.message.reply_text("❌ Unknown event name.")

    try:
        row = event_sheet.find(name).row
        event_sheet.update_cell(row, 3, "1")
    except:
        event_sheet.append_row([name, found["desc"], "1"])

    await update.message.reply_text(f"🌟 *{name}* triggered successfully!", parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 16 of X)
# ── Update Player Score ─────────────────────────────────────────
def update_score(user_id: int, amount: int):
    try:
        row = rank_sheet.find(str(user_id)).row
        current = int(rank_sheet.cell(row, 2).value)
        rank_sheet.update_cell(row, 2, current + amount)
    except:
        rank_sheet.append_row([str(user_id), str(amount)])

# ── /leaderboard Command ────────────────────────────────────────
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = rank_sheet.get_all_records()
    top = sorted(rows, key=lambda x: int(x['score']), reverse=True)[:10]
    msg = "🏆 *Top Players:*\n\n"
    for i, row in enumerate(top, 1):
        msg += f"{i}. `{row['ID']}` — {row['score']} pts\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 17 of X)
# ── /spy Command ────────────────────────────────────────────────
async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /spy <user_id>")

    try:
        target_id = int(context.args[0])
        army_row = army_sheet.find(str(target_id)).row
        infantry = army_sheet.cell(army_row, 2).value
        sniper = army_sheet.cell(army_row, 3).value
        tank = army_sheet.cell(army_row, 4).value

        await update.message.reply_text(
            f"🕵️ Spy Report on `{target_id}`:\n"
            f"Infantry: {infantry}\nSniper: {sniper}\nTank: {tank}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        await update.message.reply_text("❌ Failed to retrieve spy data.")
# main.py — SkyHustle Unified Version (Part 18 of X)
# ── /trade Command ───────────────────────────────────────────────
async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        return await update.message.reply_text("Usage: /trade <user_id> <resource> <amount>")

    sender_id = str(update.effective_user.id)
    target_id, resource, amount = context.args
    resource = resource.lower()

    if resource not in ["gold", "iron", "tech"]:
        return await update.message.reply_text("❌ Invalid resource. Use: gold, iron, tech.")

    try:
        amount = int(amount)
        if amount <= 0:
            raise ValueError
    except:
        return await update.message.reply_text("❌ Amount must be a positive number.")

    try:
        # Deduct from sender
        sender_row = resources_sheet.find(sender_id).row
        col_map = {"gold": 2, "iron": 3, "tech": 4}
        sender_current = int(resources_sheet.cell(sender_row, col_map[resource]).value)

        if sender_current < amount:
            return await update.message.reply_text("❌ You don't have enough resources.")

        resources_sheet.update_cell(sender_row, col_map[resource], sender_current - amount)

        # Add to receiver
        receiver_row = resources_sheet.find(str(target_id)).row
        receiver_current = int(resources_sheet.cell(receiver_row, col_map[resource]).value)
        resources_sheet.update_cell(receiver_row, col_map[resource], receiver_current + amount)

        # Log trade
        trade_sheet.append_row([sender_id, target_id, resource, str(amount)])
        update_score(int(sender_id), 5)

        await update.message.reply_text(f"✅ You sent {amount} {resource} to `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
    except:
        return await update.message.reply_text("❌ Failed to complete trade.")
# main.py — SkyHustle Unified Version (Part 19 of X)
# ── Admin Setup ─────────────────────────────────────────────────
ADMIN_IDS = ["7737016510"]  # Replace with your actual Telegram ID

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

# ── /give_gold Command ──────────────────────────────────────────
async def give_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /give_gold <user_id> <amount>")

    try:
        target_id = str(context.args[0])
        amount = int(context.args[1])

        row = resources_sheet.find(target_id).row
        current = int(resources_sheet.cell(row, 2).value)
        resources_sheet.update_cell(row, 2, current + amount)

        await update.message.reply_text(f"✅ Gave {amount} gold to `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
    except:
        await update.message.reply_text("❌ Failed to process command.")
# main.py — SkyHustle Unified Version (Part 20 of X)
# ── Add Faction Points ──────────────────────────────────────────
def add_faction_points(faction: str, points: int):
    try:
        row = faction_sheet.find(faction).row
        current = int(faction_sheet.cell(row, 2).value)
        faction_sheet.update_cell(row, 2, current + points)
    except:
        faction_sheet.append_row([faction, str(points)])

# ── /faction_war Command ────────────────────────────────────────
async def faction_war(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = faction_sheet.get_all_records()
    msg = "⚔️ *Faction War Standings:*\n\n"

    if not records:
        for name in FACTIONS.values():
            faction_sheet.append_row([name, "0"])
            msg += f"▪️ {name} — 0 pts\n"
    else:
        sorted_factions = sorted(records, key=lambda x: int(x["Points"]), reverse=True)
        for row in sorted_factions:
            msg += f"▪️ {row['Faction']} — {row['Points']} pts\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 21 of 21)
# ── Command + Callback Registration ─────────────────────────────
# main.py — SkyHustle Unified Version (Part 22 of X)

# ── PvP Logs Sheet ─────────────────────────────────────────────
pvp_log_sheet = get_or_create_worksheet(sheet, "PvPLogs", ["Attacker", "Defender", "Power", "Result", "Timestamp"])

# ── Utility: Log PvP Battle ─────────────────────────────────────
def log_battle(attacker_id, defender_id, power, result):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    pvp_log_sheet.append_row([str(attacker_id), str(defender_id), str(power), result, timestamp])


# ── /my_battles Command ─────────────────────────────────────────
async def my_battles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    logs = pvp_log_sheet.get_all_records()
    filtered = [log for log in logs if log["Attacker"] == user_id or log["Defender"] == user_id]

    if not filtered:
        return await update.message.reply_text("⚔️ No recent PvP activity found.")

    msg = "📜 *Your Recent Battles:*\n\n"
    for log in filtered[-10:][::-1]:
        msg += (f"▪️ [{log['Timestamp']}] {log['Attacker']} vs {log['Defender']} "
                f"({log['Power']} power) → *{log['Result']}*\n")
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 23 of X)
# ── Referrals Sheet ─────────────────────────────────────────────
referral_sheet = get_or_create_worksheet(sheet, "Referrals", ["Referrer", "Referred"])

# ── /refer Command ──────────────────────────────────────────────
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        return await update.message.reply_text("Usage: /refer <referrer_user_id>")

    referrer = context.args[0]
    if referrer == user_id:
        return await update.message.reply_text("❌ You cannot refer yourself.")

    # Prevent duplicate referrals
    rows = referral_sheet.get_all_records()
    if any(row["Referred"] == user_id for row in rows):
        return await update.message.reply_text("⚠️ Referral already used.")

    referral_sheet.append_row([referrer, user_id])

    # Reward both players
    for uid in [referrer, user_id]:
        try:
            row = resources_sheet.find(str(uid)).row
            current = int(resources_sheet.cell(row, 2).value)
            resources_sheet.update_cell(row, 2, current + 100)
            update_score(int(uid), 5)
        except:
            continue

    await update.message.reply_text("🎉 Referral successful! Both users received 100 gold.")
# main.py — SkyHustle Unified Version (Part 24 of X)
# ── Timers Sheet for Construction ───────────────────────────────
timer_sheet = get_or_create_worksheet(sheet, "Timers", ["ID", "Name", "EndsAt"])

# ── /build <name> <duration_in_min> ─────────────────────────────
async def build_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /build <building_name> <duration_in_minutes>")

    name = context.args[0]
    try:
        duration = int(context.args[1])
    except ValueError:
        return await update.message.reply_text("❌ Invalid duration.")

    end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)
    timestamp = end_time.isoformat()

    # Remove old timer if exists
    try:
        row = timer_sheet.find(user_id).row
        timer_sheet.delete_rows(row)
    except:
        pass

    timer_sheet.append_row([user_id, name, timestamp])
    await update.message.reply_text(f"🔧 Building *{name}* started. Ends in {duration} min.", parse_mode=ParseMode.MARKDOWN)

# ── /status Command ─────────────────────────────────────────────
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        row = timer_sheet.find(user_id).row
        name = timer_sheet.cell(row, 2).value
        ends_at = datetime.datetime.fromisoformat(timer_sheet.cell(row, 3).value)
        now = datetime.datetime.utcnow()
        remaining = (ends_at - now).total_seconds()

        if remaining <= 0:
            timer_sheet.delete_rows(row)
            await update.message.reply_text(f"✅ *{name}* construction completed!", parse_mode=ParseMode.MARKDOWN)
        else:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(
                f"⏳ *{name}* will complete in {mins}m {secs}s.",
                parse_mode=ParseMode.MARKDOWN
            )
    except:
        await update.message.reply_text("📭 No active construction timer.")
# main.py — SkyHustle Unified Version (Part 25 of X)
# ── BM Crate Logic ──────────────────────────────────────────────
BM_CRATE_REWARDS = [
    {"type": "gold", "amount": 200},
    {"type": "iron", "amount": 150},
    {"type": "tech", "amount": 100},
    {"type": "infantry", "amount": 3},
    {"type": "sniper", "amount": 2},
    {"type": "tank", "amount": 1},
]


# ── /setname Command ─────────────────────────────────────────────
async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        return await update.message.reply_text("Usage: /setname <your_name>")

    new_name = " ".join(context.args).strip()[:20]  # limit to 20 characters

    try:
        row = players_sheet.find(user_id).row
        players_sheet.update_cell(row, 2, new_name)
        await update.message.reply_text(f"✅ Name set to *{new_name}*!", parse_mode=ParseMode.MARKDOWN)
    except:
        await update.message.reply_text("❌ Could not update your name.")

# ── /bmcrate Command ────────────────────────────────────────────
async def bmcrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    reward = random.choice(BM_CRATE_REWARDS)

    if reward["type"] in ["gold", "iron", "tech"]:
        row = resources_sheet.find(user_id).row
        col_map = {"gold": 2, "iron": 3, "tech": 4}
        col = col_map[reward["type"]]
        current = int(resources_sheet.cell(row, col).value)
        resources_sheet.update_cell(row, col, current + reward["amount"])
    else:
        row = army_sheet.find(user_id).row
        col_map = {"infantry": 2, "sniper": 3, "tank": 4}
        col = col_map[reward["type"]]
        current = int(army_sheet.cell(row, col).value)
        army_sheet.update_cell(row, col, current + reward["amount"])

    await update.message.reply_text(
        f"🎁 You opened a BM Crate and received:\n+{reward['amount']} {reward['type'].capitalize()}!",
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("research", research))
    app.add_handler(CommandHandler("collect", collect))
    app.add_handler(CommandHandler("zones", zones))
    app.add_handler(CommandHandler("capture", capture))
    app.add_handler(CommandHandler("missions", missions))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("faction", faction))
    app.add_handler(CommandHandler("base", base))
    app.add_handler(CommandHandler("expand", expand))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("blackmarket", blackmarket))
    app.add_handler(CommandHandler("spy", spy))
    app.add_handler(CommandHandler("inbox", inbox))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CommandHandler("fight", fight))
    app.add_handler(CommandHandler("event", event))
    app.add_handler(CommandHandler("trigger_event", trigger_event))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("trade", trade))
    app.add_handler(CommandHandler("give_gold", give_gold))
    app.add_handler(CommandHandler("faction_war", faction_war))

    # Callback Queries
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(build_menu, pattern="^build_menu$"))
    app.add_handler(CallbackQueryHandler(handle_build_action, pattern="^build_"))
    app.add_handler(CallbackQueryHandler(train_menu, pattern="^train_menu$"))
    app.add_handler(CallbackQueryHandler(handle_train_action, pattern="^train_"))
    app.add_handler(CallbackQueryHandler(attack_menu, pattern="^attack_menu$"))
    app.add_handler(CallbackQueryHandler(faction, pattern="^faction_menu$"))
    app.add_handler(CallbackQueryHandler(handle_faction_choice, pattern="^faction_"))
    app.add_handler(CallbackQueryHandler(blackmarket, pattern="^store_menu$"))
    app.add_handler(CallbackQueryHandler(handle_blackmarket, pattern="^bm_"))
    app.add_handler(CallbackQueryHandler(missions, pattern="^mission_menu$"))
    app.add_handler(CallbackQueryHandler(inbox, pattern="^inbox_menu$"))
    app.add_handler(CallbackQueryHandler(event, pattern="^event_menu$"))
    app.add_handler(CallbackQueryHandler(base, pattern="^base_menu$"))
    app.add_handler(CallbackQueryHandler(leaderboard, pattern="^rank_menu$"))
    app.add_handler(CallbackQueryHandler(zones, pattern="^zone_menu$"))
    app.add_handler(CallbackQueryHandler(research, pattern="^research_menu$"))

    app.add_handler(CommandHandler("setname", setname))
    app.add_handler(CommandHandler("bmcrate", bmcrate))
    app.add_handler(CommandHandler("my_battles", my_battles))

    app.run_polling()

# ── Launch Bot ──────────────────────────────────────────────────
if __name__ == "__main__":
    main()
















