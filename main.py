# ===============================
# SkyHustle: HyperClean Part 1
# ===============================

import os
import json
import base64
import asyncio
from datetime import datetime, timedelta, date
import random

import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ===============================
# Configuration - Environment Variables
# ===============================

#   Ensure you have these set in your environment:
#   - BOT_TOKEN: Your Telegram Bot Token
#   - GOOGLE_CREDENTIALS_BASE64: Base64 encoded JSON of your Google Service Account credentials

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit"  # Replace with your sheet URL

# ===============================
# Google Sheets Setup
# ===============================

def get_sheet():
    """Connects to the Google Sheet."""

    try:
        creds_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode("utf-8")
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        return client.open_by_url(SHEET_URL)
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None  # Handle the error appropriately in your app

players_sheet = get_sheet().worksheet("SkyHustle")  # Assuming a worksheet named "SkyHustle"
zones = {"Alpha": None, "Beta": None, "Gamma": None, "Delta": None, "Epsilon": None}  # Zone control (zone: chat_id)
enabled_zones = list(zones.keys())  # For easier zone validation

# ===============================
# Player Data Management
# ===============================

class Player:
    """Represents a player in the game."""

    def __init__(self, data):
        self.chat_id = int(data.get("ChatID", 0))
        self.name = data.get("Name", "")
        self.ore = int(data.get("Ore", 0))
        self.energy = int(data.get("Energy", 100))
        self.credits = int(data.get("Credits", 100))
        self.army = json.loads(data.get("Army", '{"scout": 0, "tank": 0, "drone": 0}'))
        self.zone = data.get("Zone", "")
        self.shield_until = data.get("ShieldUntil", None)
        self.daily_streak = int(data.get("DailyStreak", 0))
        self.last_daily = data.get("LastDaily", "")
        self.black_market_unlocked = bool(data.get("BlackMarketUnlocked", False))
        self.items = json.loads(data.get("Items", "{}"))
        self.missions = json.loads(data.get("Missions", '{}')) if data.get("Missions") else {}
        self.last_mission_reset = data.get("LastMissionReset", "")
        self.row_number = int(data.get("_row", 0))  # Google Sheet row number (if applicable)
        self.wins = int(data.get("Wins", 0))
        self.losses = int(data.get("Losses", 0))
        self.banner = data.get("Banner", "")
        self.refinery_level = int(data.get("RefineryLevel", 0))
        self.lab_level = int(data.get("LabLevel", 0))
        self.defense_level = int(data.get("DefenseLevel", 0))
        self.research = json.loads(data.get("Research", '{"speed": 0, "armor": 0}')) if data.get("Research") else {}
        self.faction = data.get("Faction", None)

    def to_list(self):
        """Converts player data to a list for saving to the sheet."""
        return [
            self.chat_id,
            self.name,
            self.ore,
            self.energy,
            self.credits,
            json.dumps(self.army),
            self.zone,
            self.shield_until,
            self.daily_streak,
            self.last_daily,
            self.black_market_unlocked,
            json.dumps(self.items),
            json.dumps(self.missions),
            self.last_mission_reset,
            self.wins,
            self.losses,
            self.banner,
            self.refinery_level,
            self.lab_level,
            self.defense_level,
            json.dumps(self.research),
            self.faction,
        ]

def get_all_players():
    """Fetches all player data from the sheet and returns a list of Player objects."""

    try:
        records = players_sheet.get_all_records()
        return [Player(row) for row in records]
    except Exception as e:
        print(f"Error fetching all players: {e}")
        return []

def find_player_by_chat_id(cid):
    """Finds a player by their chat ID."""

    players = get_all_players()
    for player in players:
        if player.chat_id == cid:
            return player
    return None

def find_player_by_name(name):
    """Finds a player by their name (alias)."""

    players = get_all_players()
    for player in players:
        if player.name.lower() == name.lower():
            return player
    return None

def save_player(player):
    """Saves a player's data back to the Google Sheet."""

    try:
        if player.row_number:
            players_sheet.update(
                f"A{player.row_number}:V{player.row_number}", [player.to_list()]
            )
        else:
            #  Handle new player save (append)
            new_row = player.to_list()
            players_sheet.append_row(new_row)
            #  Update the player's row number after appending
            player.row_number = len(players_sheet.get_all_records()) + 1
    except Exception as e:
        print(f"Error saving player {player.name}: {e}")

def create_new_player(cid):
    """Creates a new player in the Google Sheet."""

    new_player_data = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": json.dumps({"scout": 0, "tank": 0, "drone": 0}),
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": "",
        "BlackMarketUnlocked": False,
        "Items": json.dumps({}),
        "Missions": json.dumps({}),
        "LastMissionReset": "",
        "Wins": 0,
        "Losses": 0,
        "Banner": "",
        "RefineryLevel": 0,
        "LabLevel": 0,
        "DefenseLevel": 0,
        "Research": json.dumps({}),
        "Faction": None,
    }
    try:
        players_sheet.append_row(list(new_player_data.values()))
        new_player = Player(find_player_by_chat_id(cid).__dict__)  # Fetch and create Player object
        return new_player
    except Exception as e:
        print(f"Error creating new player: {e}")
        return None

def find_or_create_player(cid):
    """Finds a player by chat ID, or creates a new one if not found."""

    player = find_player_by_chat_id(cid)
    if not player:
        player = create_new_player(cid)
    return player

# ===============================
# Helper Functions
# ===============================

def can_attack(player, target):
    """Checks if a player can attack another player."""

    if not target:
        return False, "Target player not found."
    if player.chat_id == target.chat_id:
        return False, "You cannot attack yourself."
    if target.shield_until and datetime.fromisoformat(target.shield_until) > datetime.now():
        return False, f"{target.name} is currently shielded."
    return True, ""

def find_zone_owner(zone):
    """Finds the player who owns a specific zone."""

    players = get_all_players()
    for player in players:
        if player.zone == zone:
            return player
    return None

def black_market_price(item):
    """Returns the price of a Black Market item."""

    prices = {"infinityscout": 100, "reviveall": 500, "hazmat": 250}
    return prices.get(item, 0)

def check_mission_progress(player, action, amount=1):
    """Checks and updates mission progress for a player."""

    today = date.today()
    if player.last_mission_reset != str(today):
        reset_missions(player)  # Reset missions if it's a new day

    if not player.missions:
        return  # No missions to check

    if action == "mine" and "mine5" in player.missions and not player.missions["mine5"]:
        player.missions["mine5"] = player.missions.get("mine5", 0) + amount >= 5
        if player.missions["mine5"]:
            player.credits += 50  # Reward for completing mission
    elif action == "win" and "win1" in player.missions and not player.missions["win1"]:
        player.missions["win1"] = True
        player.credits += 75
    elif action == "forge" and "forge5" in player.missions and not player.missions["forge5"]:
        player.missions["forge5"] = player.missions.get("forge5", 0) + amount >= 5
        if player.missions["forge5"]:
            player.credits += 60
    save_player(player)

def reset_missions(player):
    """Resets daily missions for a player."""

    player.missions = {
        "mine5": False,
        "win1": False,
        "forge5": False,
    }  # Reset mission status
    player.last_mission_reset = str(date.today())
    save_player(player)

def calculate_attack_damage(attacker, defender):
    """Calculates the damage in an attack."""

    attacker_power = (
        attacker.army["scout"] * 1 +
        attacker.army["tank"] * 3 +
        attacker.army["drone"] * 2
    )
    defender_power = (
        defender.army["scout"] * 1 +
        defender.army["tank"] * 3 +
        defender.army["drone"] * 2
    )

    # Apply research bonuses
    attacker_power *= 1 + (attacker.research.get("speed", 0) * 0.1)
    defender_power *= 1 + (defender.research.get("armor", 0) * 0.1)

    damage = attacker_power - defender_power
    damage = max(1, damage)  # Ensure minimum damage of 1
    return damage

def apply_attack_results(attacker, defender, damage):
    """Applies the results of an attack, updating army counts."""

    attacker_loss_rate = 0.2
    defender_loss_rate = 0.3

    for unit in attacker.army:
        attacker.army[unit] = max(0, int(attacker.army[unit] * (1 - attacker_loss_rate)))
    for unit in defender.army:
        defender.army[unit] = max(0, int(defender.army[unit] * (1 - defender_loss_rate)))

    # Reduce more units based on damage
    total_defender_units = sum(defender.army.values())
    damage_reduction_ratio = min(1, damage / (total_defender_units + 1e-6))  # Avoid division by zero
    for unit in defender.army:
        defender.army[unit] = max(0, int(defender.army[unit] * (1 - damage_reduction_ratio)))

    save_player(attacker)
    save_player(defender)

# ===============================
# Command Handlers
# ===============================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /start command."""

    intro = (
        "🌌 *Welcome to SkyHustle!*\n"
        "Centuries from now, the Hyperion core pulses with boundless energy.\n"
        "You are a Commander in the New Galactic Order.\n"
        "Gather ore, strengthen your army, dominate the zones.\n\n"
        "💠 Use /name <alias> to set your callsign.\n"
        "💠 Use /status to view your progress.\n"
        "💠 Use /mine ore 1 to start mining resources.\n\n"
        "🛡 Glory and power await!"
    )
    await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

async def name_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /name command."""

    text = update.message.text
    alias = text[6:].strip()
    if not alias:
        await update.message.reply_text("⚠️ Usage: /name <alias>")
        return

    existing_player = find_player_by_name(alias)
    if existing_player and existing_player.chat_id != player.chat_id:
        await update.message.reply_text("❌ That alias is already taken.")
        return

    player.name = alias
    save_player(player)
    await update.message.reply_text(f"✅ Callsign set to *{alias}*!", parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /status command."""

    shield = player.shield_until if player.shield_until else "None"
    msg = (
        f"📊 *Commander {player.name or 'Unnamed'}*\n"
        f"🪨 Ore: {player.ore} | ⚡ Energy: {player.energy} | 💳 Credits: {player.credits}\n"
        f"🛡 Shield Until: {shield}\n"
        f"⚔ Army: {player.army}\n"
        f"🎁 Items: {player.items or 'None'}\n"
        f"🌍 Zone: {player.zone or 'None'}\n"
        f"Wins: {player.wins} | Losses: {player.losses}\n"
        f"Refinery Level: {player.refinery_level}\n"
        f"Lab Level: {player.lab_level}\n"
# ===============================
# SkyHustle: HyperClean Part 2
# ===============================

#   (Part 1 code goes here - do not repeat it)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /daily command."""

    today = date.today()
    if player.last_daily == str(today):
        await update.message.reply_text("🎁 You've already claimed your daily reward today.")
        return

    last_daily = datetime.strptime(player.last_daily, "%Y-%m-%d").date() if player.last_daily else None
    player.credits += 50
    player.energy += 20
    player.daily_streak = player.daily_streak + 1 if last_daily == today - timedelta(days=1) else 1
    player.last_daily = str(today)
    save_player(player)
    await update.message.reply_text(f"🎉 +50 Credits, +20 Energy! Streak: {player.daily_streak} days.")

async def mine_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /mine command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 3 or parts[1] != "ore":
        await update.message.reply_text("⚠️ Usage: /mine ore <count>")
        return
    try:
        count = int(parts[2])
    except ValueError:
        await update.message.reply_text("⚠️ Count must be a number.")
        return

    if player.energy < count * 5:
        await update.message.reply_text("⚠️ Not enough energy.")
        return

    ore_gain = 20 * count + (player.refinery_level * 5)
    credits_gain = 10 * count
    player.ore += ore_gain
    player.credits += credits_gain
    player.energy -= count * 5
    save_player(player)
    check_mission_progress(player, "mine", ore_gain)  # Track mission progress
    await update.message.reply_text(f"⛏️ Mined {ore_gain} Ore and earned {credits_gain} Credits.")

async def forge_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /forge command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 3:
        await update.message.reply_text("⚒️ Usage: /forge <unit> <count>")
        return

    unit, count = parts[1], parts[2]
    try:
        count = int(count)
    except ValueError:
        await update.message.reply_text("⚒️ Count must be a number.")
        return

    if unit not in ["scout", "tank", "drone"]:
        await update.message.reply_text("⚒️ Invalid unit. Choose scout, tank, or drone.")
        return

    cost_ore, cost_credits = {"scout": (10, 5), "tank": (30, 20), "drone": (20, 10)}[unit]
    if player.ore < cost_ore * count or player.credits < cost_credits * count:
        await update.message.reply_text("⚠️ Not enough Ore or Credits.")
        return

    player.army[unit] = player.army.get(unit, 0) + count
    player.ore -= cost_ore * count
    player.credits -= cost_credits * count
    save_player(player)
    check_mission_progress(player, "forge", count)  # Track mission progress
    await update.message.reply_text(f"✅ Forged {count} {unit}(s)!")

async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /use command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("🛡️ Usage: /use <item>")
        return

    item_id = parts[1]

    if item_id not in player.items or player.items[item_id] <= 0:
        await update.message.reply_text("⚠️ You don't own that item or have none left.")
        return

    # Perishable item logic
    if item_id.startswith("infinityscout") or item_id == "reviveall":
        player.items[item_id] -= 1
        if player.items[item_id] <= 0:
            del player.items[item_id]

    if item_id == "reviveall":
        for unit in player.army:
            player.army[unit] += 5
        await update.message.reply_text("🛡️ All standard army units revived!")

    if item_id == "hazmat":
        await update.message.reply_text("☢️ Your units are now radiation-proof for zone exploration!")

    save_player(player)
    await update.message.reply_text(f"✅ Used {item_id}.")

async def unlockbm_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /unlockbm command."""

    if player.black_market_unlocked:
        await update.message.reply_text("✅ Black Market already unlocked!")
        return
    if player.credits < 1000:
        await update.message.reply_text("💳 Need 1000 credits to unlock the Black Market.")
        return
    player.credits -= 1000
    player.black_market_unlocked = True
    save_player(player)
    await update.message.reply_text("🖤 Black Market access unlocked!")

async def blackmarket_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /blackmarket command."""

    if not player.black_market_unlocked:
        await update.message.reply_text("🔒 Black Market is locked. Use /unlockbm first.")
        return
    shop = (
        "🖤 *Black Market Deals:*\n"
        "`/buy infinityscout` - 100 credits\n"
        "`/buy reviveall` - 500 credits\n"
        "`/buy hazmat` - 250 credits\n"
        "\nUse `/buy <item>` to purchase."
    )
    await update.message.reply_text(shop, parse_mode=ParseMode.MARKDOWN)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /buy command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("🛒 Usage: /buy <item>")
        return
    item = parts[1]

    if not player.black_market_unlocked:
        await update.message.reply_text("🔒 Unlock Black Market first.")
        return

    price = black_market_price(item)
    if not price:
        await update.message.reply_text("❌ Item not found in Black Market.")
        return

    if player.credits < price:
        await update.message.reply_text("💳 Not enough credits.")
        return

    player.credits -= price
    player.items[item] = player.items.get(item, 0) + 1
    save_player(player)

    await update.message.reply_text(f"🛒 Purchased {item} successfully!")

# ===============================
# Helper Command
# ===============================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help for all commands"""
    await update.message.reply_text(
        "📜 *Available Commands:*\\n"\
        "`/start` - Start your journey\\n"\
        "`/name <alias>` - Set your commander name\\n"\
        "`/status` - View your stats\\n"\
        "`/mine ore <amount>` - Mine Hyperion ore\\n"\
        "`/forge <unit> <count>` - Build units\\n"\
        "`/daily` - Claim your daily rewards\\n"\
        "`/claim <zone>` - Claim a zone\\n"\
        "`/map` - View zone map\\n"\
        "`/missions` - View missions\\n"\
        "`/blackmarket` - Open premium store\\n"\
        "`/buy <item>` - Purchase Black Market item\\n"\
        "`/unlockbm` - Unlock Black Market\\n"\
        "`/attack <player>` - Attack enemy commander\\n"\
        "`/rules` - Show game rules\\n"\
        "`/help` - Show this list\\n",
        parse_mode=ParseMode.MARKDOWN
    )

# 📜 Rules Command
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 *SkyHustle Universal Laws:*\\n"\
        "- Respect zones and their owners.\\n"\
        "- No griefing or abuse.\\n"\
        "- Play fair, play smart.\\n"\
        "- Wars are ruthless but honor matters.\\n"\
        "- Exploits/cheats = permanent ban.\\n\\n"\
        "💬 Questions? Contact the SkyCouncil!",
        parse_mode=ParseMode.MARKDOWN
    )
async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /map command."""

    zones_status = "🌍 *Zone Control Map:*\n"
    for zone in enabled_zones:
        owner = find_zone_owner(zone)
        if owner:
            zones_status += f"🔸 {zone}: {owner.name}\n"
        else:
            zones_status += f"🔹 {zone}: Unclaimed\n"
    await update.message.reply_text(zones_status, parse_mode=ParseMode.MARKDOWN)

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /claim command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("📍 Usage: /claim <zone>")
        return

    zone_name = parts[1].capitalize()
    if zone_name not in enabled_zones:
        await update.message.reply_text("❌ Invalid zone.")
        return

    if find_zone_owner(zone_name):
        await update.message.reply_text("⚠️ Zone already claimed.")
        return

    if player.credits < 100:
        await update.message.reply_text("💳 Need at least 100 credits to claim a zone.")
        return

    player.zone = zone_name
    player.credits -= 100
    save_player(player)

    await update.message.reply_text(f"🏴 Successfully claimed {zone_name}!")

async def missions_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /missions command."""

    today = date.today()
    missions_text = "🎯 *Current Missions:*\n"
    missions_data = {
        "mine5": {"desc": "Mine 5 ores today", "reward": 50},
        "win1": {"desc": "Win 1 attack today", "reward": 75},
        "forge5": {"desc": "Forge 5 units today", "reward": 60},
    }

    # Initialize player missions if empty or new day
    if not player.missions or player.last_mission_reset != str(today):
        player.missions = {k: False for k in missions_data.keys()}
        player.last_mission_reset = str(today)
        save_player(player)

    for mission_id, status in player.missions.items():
        completed = "✅" if status else "❌"
        missions_text += f"{completed} {missions_data[mission_id]['desc']} (+{missions_data[mission_id]['reward']} credits)\n"

    missions_text += "\n_Complete missions and earn credits!_"

    await update.message.reply_text(missions_text, parse_mode=ParseMode.MARKDOWN)

# ===============================
# Main Message Handler
# ===============================

COMMAND_HANDLERS = {
    "/start": start_command,
    "/name": name_command,
    "/status": status_command,
    "/daily": daily_command,
    "/mine": mine_command,
    "/forge": forge_command,
    "/use": use_command,
    "/unlockbm": unlockbm_command,
    "/blackmarket": blackmarket_command,
    "/buy": buy_command,
    "/map": map_command,
    "/claim": claim_command,
    "/missions": missions_command,
    "/help": help_command,
    "/rules": rules_command,
    # ... (Add the attack command here in Part 4)
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all incoming messages."""

    if not update.message:
        return

    text = update.message.text.strip()
    cid = update.message.chat_id

    player = find_or_create_player(cid)  # Ensure player exists

    for command, handler in COMMAND_HANDLERS.items():
        if text.startswith(command):
            try:
                await handler(update, context, player)
            except Exception as e:
                print(f"Error handling command {command}: {e}")
                await update.message.reply_text(
                    "⚠️ An error occurred. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            return  # Stop processing after handling the command
# ===============================
# SkyHustle: HyperClean Part 1
# ===============================

import os
import json
import base64
import asyncio
from datetime import datetime, timedelta, date
import random

import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ===============================
# Configuration - Environment Variables
# ===============================

#   Ensure you have these set in your environment:
#   - BOT_TOKEN: Your Telegram Bot Token
#   - GOOGLE_CREDENTIALS_BASE64: Base64 encoded JSON of your Google Service Account credentials

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit"  # Replace with your sheet URL

# ===============================
# Google Sheets Setup
# ===============================

def get_sheet():
    """Connects to the Google Sheet."""

    try:
        creds_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode("utf-8")
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        return client.open_by_url(SHEET_URL)
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None  # Handle the error appropriately in your app

players_sheet = get_sheet().worksheet("SkyHustle")  # Assuming a worksheet named "SkyHustle"
zones = {"Alpha": None, "Beta": None, "Gamma": None, "Delta": None, "Epsilon": None}  # Zone control (zone: chat_id)
enabled_zones = list(zones.keys())  # For easier zone validation

# ===============================
# Player Data Management
# ===============================

class Player:
    """Represents a player in the game."""

    def __init__(self, data):
        self.chat_id = int(data.get("ChatID", 0))
        self.name = data.get("Name", "")
        self.ore = int(data.get("Ore", 0))
        self.energy = int(data.get("Energy", 100))
        self.credits = int(data.get("Credits", 100))
        self.army = json.loads(data.get("Army", '{"scout": 0, "tank": 0, "drone": 0}'))
        self.zone = data.get("Zone", "")
        self.shield_until = data.get("ShieldUntil", None)
        self.daily_streak = int(data.get("DailyStreak", 0))
        self.last_daily = data.get("LastDaily", "")
        self.black_market_unlocked = bool(data.get("BlackMarketUnlocked", False))
        self.items = json.loads(data.get("Items", "{}"))
        self.missions = json.loads(data.get("Missions", '{}')) if data.get("Missions") else {}
        self.last_mission_reset = data.get("LastMissionReset", "")
        self.row_number = int(data.get("_row", 0))  # Google Sheet row number (if applicable)
        self.wins = int(data.get("Wins", 0))
        self.losses = int(data.get("Losses", 0))
        self.banner = data.get("Banner", "")
        self.refinery_level = int(data.get("RefineryLevel", 0))
        self.lab_level = int(data.get("LabLevel", 0))
        self.defense_level = int(data.get("DefenseLevel", 0))
        self.research = json.loads(data.get("Research", '{"speed": 0, "armor": 0}')) if data.get("Research") else {}
        self.faction = data.get("Faction", None)

    def to_list(self):
        """Converts player data to a list for saving to the sheet."""
        return [
            self.chat_id,
            self.name,
            self.ore,
            self.energy,
            self.credits,
            json.dumps(self.army),
            self.zone,
            self.shield_until,
            self.daily_streak,
            self.last_daily,
            self.black_market_unlocked,
            json.dumps(self.items),
            json.dumps(self.missions),
            self.last_mission_reset,
            self.wins,
            self.losses,
            self.banner,
            self.refinery_level,
            self.lab_level,
            self.defense_level,
            json.dumps(self.research),
            self.faction,
        ]

def get_all_players():
    """Fetches all player data from the sheet and returns a list of Player objects."""

    try:
        records = players_sheet.get_all_records()
        return [Player(row) for row in records]
    except Exception as e:
        print(f"Error fetching all players: {e}")
        return []

def find_player_by_chat_id(cid):
    """Finds a player by their chat ID."""

    players = get_all_players()
    for player in players:
        if player.chat_id == cid:
            return player
    return None

def find_player_by_name(name):
    """Finds a player by their name (alias)."""

    players = get_all_players()
    for player in players:
        if player.name.lower() == name.lower():
            return player
    return None

def save_player(player):
    """Saves a player's data back to the Google Sheet."""

    try:
        if player.row_number:
            players_sheet.update(
                f"A{player.row_number}:V{player.row_number}", [player.to_list()]
            )
        else:
            #  Handle new player save (append)
            new_row = player.to_list()
            players_sheet.append_row(new_row)
            #  Update the player's row number after appending
            player.row_number = len(players_sheet.get_all_records()) + 1
    except Exception as e:
        print(f"Error saving player {player.name}: {e}")

def create_new_player(cid):
    """Creates a new player in the Google Sheet."""

    new_player_data = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": json.dumps({"scout": 0, "tank": 0, "drone": 0}),
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": "",
        "BlackMarketUnlocked": False,
        "Items": json.dumps({}),
        "Missions": json.dumps({}),
        "LastMissionReset": "",
        "Wins": 0,
        "Losses": 0,
        "Banner": "",
        "RefineryLevel": 0,
        "LabLevel": 0,
        "DefenseLevel": 0,
        "Research": json.dumps({}),
        "Faction": None,
    }
    try:
        players_sheet.append_row(list(new_player_data.values()))
        new_player = Player(find_player_by_chat_id(cid).__dict__)  # Fetch and create Player object
        return new_player
    except Exception as e:
        print(f"Error creating new player: {e}")
        return None

def find_or_create_player(cid):
    """Finds a player by chat ID, or creates a new one if not found."""

    player = find_player_by_chat_id(cid)
    if not player:
        player = create_new_player(cid)
    return player

# ===============================
# Helper Functions
# ===============================

def can_attack(player, target):
    """Checks if a player can attack another player."""

    if not target:
        return False, "Target player not found."
    if player.chat_id == target.chat_id:
        return False, "You cannot attack yourself."
    if target.shield_until and datetime.fromisoformat(target.shield_until) > datetime.now():
        return False, f"{target.name} is currently shielded."
    return True, ""

def find_zone_owner(zone):
    """Finds the player who owns a specific zone."""

    players = get_all_players()
    for player in players:
        if player.zone == zone:
            return player
    return None

def black_market_price(item):
    """Returns the price of a Black Market item."""

    prices = {"infinityscout": 100, "reviveall": 500, "hazmat": 250}
    return prices.get(item, 0)

def check_mission_progress(player, action, amount=1):
    """Checks and updates mission progress for a player."""

    today = date.today()
    if player.last_mission_reset != str(today):
        reset_missions(player)  # Reset missions if it's a new day

    if not player.missions:
        return  # No missions to check

    if action == "mine" and "mine5" in player.missions and not player.missions["mine5"]:
        player.missions["mine5"] = player.missions.get("mine5", 0) + amount >= 5
        if player.missions["mine5"]:
            player.credits += 50  # Reward for completing mission
    elif action == "win" and "win1" in player.missions and not player.missions["win1"]:
        player.missions["win1"] = True
        player.credits += 75
    elif action == "forge" and "forge5" in player.missions and not player.missions["forge5"]:
        player.missions["forge5"] = player.missions.get("forge5", 0) + amount >= 5
        if player.missions["forge5"]:
            player.credits += 60
    save_player(player)

def reset_missions(player):
    """Resets daily missions for a player."""

    player.missions = {
        "mine5": False,
        "win1": False,
        "forge5": False,
    }  # Reset mission status
    player.last_mission_reset = str(date.today())
    save_player(player)

def calculate_attack_damage(attacker, defender):
    """Calculates the damage in an attack."""

    attacker_power = (
        attacker.army["scout"] * 1 +
        attacker.army["tank"] * 3 +
        attacker.army["drone"] * 2
    )
    defender_power = (
        defender.army["scout"] * 1 +
        defender.army["tank"] * 3 +
        defender.army["drone"] * 2
    )

    # Apply research bonuses
    attacker_power *= 1 + (attacker.research.get("speed", 0) * 0.1)
    defender_power *= 1 + (defender.research.get("armor", 0) * 0.1)

    damage = attacker_power - defender_power
    damage = max(1, damage)  # Ensure minimum damage of 1
    return damage

def apply_attack_results(attacker, defender, damage):
    """Applies the results of an attack, updating army counts."""

    attacker_loss_rate = 0.2
    defender_loss_rate = 0.3

    for unit in attacker.army:
        attacker.army[unit] = max(0, int(attacker.army[unit] * (1 - attacker_loss_rate)))
    for unit in defender.army:
        defender.army[unit] = max(0, int(defender.army[unit] * (1 - defender_loss_rate)))

    # Reduce more units based on damage
    total_defender_units = sum(defender.army.values())
    damage_reduction_ratio = min(1, damage / (total_defender_units + 1e-6))  # Avoid division by zero
    for unit in defender.army:
        defender.army[unit] = max(0, int(defender.army[unit] * (1 - damage_reduction_ratio)))

    save_player(attacker)
    save_player(defender)

# ===============================
# Command Handlers
# ===============================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /start command."""

    intro = (
        "🌌 *Welcome to SkyHustle!*\n"
        "Centuries from now, the Hyperion core pulses with boundless energy.\n"
        "You are a Commander in the New Galactic Order.\n"
        "Gather ore, strengthen your army, dominate the zones.\n\n"
        "💠 Use /name <alias> to set your callsign.\n"
        "💠 Use /status to view your progress.\n"
        "💠 Use /mine ore 1 to start mining resources.\n\n"
        "🛡 Glory and power await!"
    )
    await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

async def name_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /name command."""

    text = update.message.text
    alias = text[6:].strip()
    if not alias:
        await update.message.reply_text("⚠️ Usage: /name <alias>")
        return

    existing_player = find_player_by_name(alias)
    if existing_player and existing_player.chat_id != player.chat_id:
        await update.message.reply_text("❌ That alias is already taken.")
        return

    player.name = alias
    save_player(player)
    await update.message.reply_text(f"✅ Callsign set to *{alias}*!", parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /status command."""

    shield = player.shield_until if player.shield_until else "None"
    msg = (
        f"📊 *Commander {player.name or 'Unnamed'}*\n"
        f"🪨 Ore: {player.ore} | ⚡ Energy: {player.energy} | 💳 Credits: {player.credits}\n"
        f"🛡 Shield Until: {shield}\n"
        f"⚔ Army: {player.army}\n"
        f"🎁 Items: {player.items or 'None'}\n"
        f"🌍 Zone: {player.zone or 'None'}\n"
        f"Wins: {player.wins} | Losses: {player.losses}\n"
        f"Refinery Level: {player.refinery_level}\n"
        f"Lab Level: {player.lab_level}\n"
continue to part 2 a natural continuation from part 1



Okay, here's Part 2, continuing directly from where Part 1 left off. This part adds more command handlers, including those for mining, forging, using items, and some Black Market functionality:

Python

# ===============================
# SkyHustle: HyperClean Part 2
# ===============================

#   (Part 1 code goes here - do not repeat it)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /daily command."""

    today = date.today()
    if player.last_daily == str(today):
        await update.message.reply_text("🎁 You've already claimed your daily reward today.")
        return

    last_daily = datetime.strptime(player.last_daily, "%Y-%m-%d").date() if player.last_daily else None
    player.credits += 50
    player.energy += 20
    player.daily_streak = player.daily_streak + 1 if last_daily == today - timedelta(days=1) else 1
    player.last_daily = str(today)
    save_player(player)
    await update.message.reply_text(f"🎉 +50 Credits, +20 Energy! Streak: {player.daily_streak} days.")

async def mine_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /mine command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 3 or parts[1] != "ore":
        await update.message.reply_text("⚠️ Usage: /mine ore <count>")
        return
    try:
        count = int(parts[2])
    except ValueError:
        await update.message.reply_text("⚠️ Count must be a number.")
        return

    if player.energy < count * 5:
        await update.message.reply_text("⚠️ Not enough energy.")
        return

    ore_gain = 20 * count + (player.refinery_level * 5)
    credits_gain = 10 * count
    player.ore += ore_gain
    player.credits += credits_gain
    player.energy -= count * 5
    save_player(player)
    check_mission_progress(player, "mine", ore_gain)  # Track mission progress
    await update.message.reply_text(f"⛏️ Mined {ore_gain} Ore and earned {credits_gain} Credits.")

async def forge_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /forge command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 3:
        await update.message.reply_text("⚒️ Usage: /forge <unit> <count>")
        return

    unit, count = parts[1], parts[2]
    try:
        count = int(count)
    except ValueError:
        await update.message.reply_text("⚒️ Count must be a number.")
        return

    if unit not in ["scout", "tank", "drone"]:
        await update.message.reply_text("⚒️ Invalid unit. Choose scout, tank, or drone.")
        return

    cost_ore, cost_credits = {"scout": (10, 5), "tank": (30, 20), "drone": (20, 10)}[unit]
    if player.ore < cost_ore * count or player.credits < cost_credits * count:
        await update.message.reply_text("⚠️ Not enough Ore or Credits.")
        return

    player.army[unit] = player.army.get(unit, 0) + count
    player.ore -= cost_ore * count
    player.credits -= cost_credits * count
    save_player(player)
    check_mission_progress(player, "forge", count)  # Track mission progress
    await update.message.reply_text(f"✅ Forged {count} {unit}(s)!")

async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /use command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("🛡️ Usage: /use <item>")
        return

    item_id = parts[1]

    if item_id not in player.items or player.items[item_id] <= 0:
        await update.message.reply_text("⚠️ You don't own that item or have none left.")
        return

    # Perishable item logic
    if item_id.startswith("infinityscout") or item_id == "reviveall":
        player.items[item_id] -= 1
        if player.items[item_id] <= 0:
            del player.items[item_id]

    if item_id == "reviveall":
        for unit in player.army:
            player.army[unit] += 5
        await update.message.reply_text("🛡️ All standard army units revived!")

    if item_id == "hazmat":
        await update.message.reply_text("☢️ Your units are now radiation-proof for zone exploration!")

    save_player(player)
    await update.message.reply_text(f"✅ Used {item_id}.")

async def unlockbm_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /unlockbm command."""

    if player.black_market_unlocked:
        await update.message.reply_text("✅ Black Market already unlocked!")
        return
    if player.credits < 1000:
        await update.message.reply_text("💳 Need 1000 credits to unlock the Black Market.")
        return
    player.credits -= 1000
    player.black_market_unlocked = True
    save_player(player)
    await update.message.reply_text("🖤 Black Market access unlocked!")

async def blackmarket_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /blackmarket command."""

    if not player.black_market_unlocked:
        await update.message.reply_text("🔒 Black Market is locked. Use /unlockbm first.")
        return
    shop = (
        "🖤 *Black Market Deals:*\n"
        "`/buy infinityscout` - 100 credits\n"
        "`/buy reviveall` - 500 credits\n"
        "`/buy hazmat` - 250 credits\n"
        "\nUse `/buy <item>` to purchase."
    )
    await update.message.reply_text(shop, parse_mode=ParseMode.MARKDOWN)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /buy command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("🛒 Usage: /buy <item>")
        return
    item = parts[1]

    if not player.black_market_unlocked:
        await update.message.reply_text("🔒 Unlock Black Market first.")
        return

    price = black_market_price(item)
    if not price:
        await update.message.reply_text("❌ Item not found in Black Market.")
        return

    if player.credits < price:
        await update.message.reply_text("💳 Not enough credits.")
        return

    player.credits -= price
    player.items[item] = player.items.get(item, 0) + 1
    save_player(player)

    await update.message.reply_text(f"🛒 Purchased {item} successfully!")

# ===============================
# Helper Command
# ===============================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help for all commands"""
    await update.message.reply_text(
        "📜 *Available Commands:*\\n"\
        "`/start` - Start your journey\\n"\
        "`/name <alias>` - Set your commander name\\n"\
        "`/status` - View your stats\\n"\
        "`/mine ore <amount>` - Mine Hyperion ore\\n"\
        "`/forge <unit> <count>` - Build units\\n"\
        "`/daily` - Claim your daily rewards\\n"\
        "`/claim <zone>` - Claim a zone\\n"\
        "`/map` - View zone map\\n"\
        "`/missions` - View missions\\n"\
        "`/blackmarket` - Open premium store\\n"\
        "`/buy <item>` - Purchase Black Market item\\n"\
        "`/unlockbm` - Unlock Black Market\\n"\
        "`/attack <player>` - Attack enemy commander\\n"\
        "`/rules` - Show game rules\\n"\
        "`/help` - Show this list\\n",
        parse_mode=ParseMode.MARKDOWN
    )

# 📜 Rules Command
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 *SkyHustle Universal Laws:*\\n"\
        "- Respect zones and their owners.\\n"\
        "- No griefing or abuse.\\n"\
        "- Play fair, play smart.\\n"\
        "- Wars are ruthless but honor matters.\\n"\
        "- Exploits/cheats = permanent ban.\\n\\n"\
        "💬 Questions? Contact the SkyCouncil!",
        parse_mode=ParseMode.MARKDOWN
    )

# App Main Loop
if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Connect extra /help and /rules commands...
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", rules_command))

    # Connect all handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("name", name_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("mine", mine_command))
    app.add_handler(CommandHandler("forge", forge_command))
    app.add_handler(CommandHandler("use", use_command))
    app.add_handler(CommandHandler("unlockbm", unlockbm_command))
    app.add_handler(CommandHandler("blackmarket", blackmarket_command))
    app.add_handler(CommandHandler("buy", buy_command))

    app.run_polling()
What Part 2 Adds:

More Command Handlers: Implements daily, mine, forge, use, unlockbm, blackmarket, and buy.
Help and Rules Commands: Adds /help and /rules for player guidance.
Main Loop Enhancements: Includes the /help and /rules command handlers in the main application.
Next Steps:

Combine Part 1 and Part 2: Copy the code from Part 2 and paste it directly after the code from Part 1. Make sure you don't accidentally duplicate any sections.
Run the Code (with setup!):
Set your environment variables (BOT_TOKEN, GOOGLE_CREDENTIALS_BASE64).
Install dependencies (pip install python-telegram-bot gspread google-auth).
Ensure your Google Sheet is set up correctly.
Run the Python script.
Test: Try the commands you've implemented so far in your Telegram bot.
Let me know when you're ready for Part 3, which will focus on zone control and missions!

ready for part 3



Alright, here's Part 3. This section adds the zone control commands (/map, /claim) and the missions command (/missions):

Python

# ===============================
# SkyHustle: HyperClean Part 3
# ===============================

#   (Part 1 and Part 2 code goes here - do not repeat it)

async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /map command."""

    zones_status = "🌍 *Zone Control Map:*\n"
    for zone in enabled_zones:
        owner = find_zone_owner(zone)
        if owner:
            zones_status += f"🔸 {zone}: {owner.name}\n"
        else:
            zones_status += f"🔹 {zone}: Unclaimed\n"
    await update.message.reply_text(zones_status, parse_mode=ParseMode.MARKDOWN)

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /claim command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("📍 Usage: /claim <zone>")
        return

    zone_name = parts[1].capitalize()
    if zone_name not in enabled_zones:
        await update.message.reply_text("❌ Invalid zone.")
        return

    if find_zone_owner(zone_name):
        await update.message.reply_text("⚠️ Zone already claimed.")
        return

    if player.credits < 100:
        await update.message.reply_text("💳 Need at least 100 credits to claim a zone.")
        return

    player.zone = zone_name
    player.credits -= 100
    save_player(player)

    await update.message.reply_text(f"🏴 Successfully claimed {zone_name}!")

async def missions_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /missions command."""

    today = date.today()
    missions_text = "🎯 *Current Missions:*\n"
    missions_data = {
        "mine5": {"desc": "Mine 5 ores today", "reward": 50},
        "win1": {"desc": "Win 1 attack today", "reward": 75},
        "forge5": {"desc": "Forge 5 units today", "reward": 60},
    }

    # Initialize player missions if empty or new day
    if not player.missions or player.last_mission_reset != str(today):
        player.missions = {k: False for k in missions_data.keys()}
        player.last_mission_reset = str(today)
        save_player(player)

    for mission_id, status in player.missions.items():
        completed = "✅" if status else "❌"
        missions_text += f"{completed} {missions_data[mission_id]['desc']} (+{missions_data[mission_id]['reward']} credits)\n"

    missions_text += "\n_Complete missions and earn credits!_"

    await update.message.reply_text(missions_text, parse_mode=ParseMode.MARKDOWN)

# ===============================
# Main Message Handler
# ===============================

COMMAND_HANDLERS = {
    "/start": start_command,
    "/name": name_command,
    "/status": status_command,
    "/daily": daily_command,
    "/mine": mine_command,
    "/forge": forge_command,
    "/use": use_command,
    "/unlockbm": unlockbm_command,
    "/blackmarket": blackmarket_command,
    "/buy": buy_command,
    "/map": map_command,
    "/claim": claim_command,
    "/missions": missions_command,
    "/help": help_command,
    "/rules": rules_command,
    # ... (Add the attack command here in Part 4)
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all incoming messages."""

    if not update.message:
        return

    text = update.message.text.strip()
    cid = update.message.chat_id

    player = find_or_create_player(cid)  # Ensure player exists

    for command, handler in COMMAND_HANDLERS.items():
        if text.startswith(command):
            try:
                await handler(update, context, player)
            except Exception as e:
                print(f"Error handling command {command}: {e}")
                await update.message.reply_text(
                    "⚠️ An error occurred. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            return  # Stop processing after handling the command

    # Handle non-command messages (you can add game logic here if needed)
    # For example, you could check for zone chat or other interactions
    # await update.message.reply_text("💬 I received your message!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Connect all handlers
    for command, handler in COMMAND_HANDLERS.items():
        app.add_handler(CommandHandler(command[1:], handler))  # Remove the leading "/"

    app.run_polling()
What Part 3 Adds:

Zone Control: Implements the /map and /claim commands, allowing players to view and claim zones.
Missions: Adds the /missions command to display daily missions.
Enhanced handle_message:
It now ensures a player object exists using find_or_create_player.
Includes basic error handling within the command processing loop.
Adds a placeholder for handling non-command messages (where you could add more complex chat interactions).
Dynamically registers command handlers from the COMMAND_HANDLERS dictionary, making it easier to add new commands.
Next Steps:

Combine All Parts: Copy the code from Part 3 and paste it after the combined code of Part 1 and Part 2.
Test: Run the bot and test the /map, /claim, and /missions commands.
Are you ready for Part 4, where we'll add the attack functionality and some building/research mechanics?

ready for part 4



Okay, here's Part 4. This is a big one, adding the attack command, shield functionality, and the building upgrade commands:

Python

# ===============================
# SkyHustle: HyperClean Part 4
# ===============================

#   (Parts 1, 2, and 3 code goes here - do not repeat it)

import asyncio
from datetime import datetime, timedelta, date
import random

# ===============================
# Attack and Shield Logic
# ===============================

def apply_shield(player, duration_hours):
    """Applies a shield to a player for a given duration."""
    shield_end = datetime.now() + timedelta(hours=duration_hours)
    player.shield_until = shield_end.isoformat()
    save_player(player)

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /attack command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("⚔️ Usage: /attack <player_name>")
        return

    target_name = parts[1]
    target = find_player_by_name(target_name)
    if not target:
        await update.message.reply_text("❌ Player not found.")
        return

    can_attack_result, reason = can_attack(player, target)
    if not can_attack_result:
        await update.message.reply_text(f"🛡️ Cannot attack: {reason}")
        return

    damage = calculate_attack_damage(player, target)
    apply_attack_results(player, target, damage)

    # Determine winner and loser (simplified)
    if damage > 0:  # Attacker wins (simplified)
        winner = player
        loser = target
    else:
        winner = target
        loser = player

    winner.wins += 1
    loser.losses += 1
    save_player(winner)
    save_player(loser)

    check_mission_progress(player, "win")  # Track mission progress

    await update.message.reply_text(
        f"💥 Attack successful! {player.name} dealt {damage} damage to {target.name}!\n"
        f"{winner.name} wins, {loser.name} loses.",
        parse_mode=ParseMode.MARKDOWN,
    )

    apply_shield(target, 2)  # Apply shield to the defender
    await context.bot.send_message(
        chat_id=target.chat_id,
        text=f"🛡️ You have been attacked and shielded for 2 hours!",
    )

# ===============================
# Building Upgrades
# ===============================

async def upgrade_refinery_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /upgraderefinery command."""

    cost = 100 * (player.refinery_level + 1)
    if player.ore < cost:
        await update.message.reply_text(f"⚠️ Not enough Ore to upgrade. Cost: {cost}")
        return

    player.ore -= cost
    player.refinery_level += 1
    save_player(player)
    await update.message.reply_text(f"🏭 Refinery upgraded to level {player.refinery_level}!")

async def upgrade_lab_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /upgradelab command."""

    cost = 150 * (player.lab_level + 1)
    if player.credits < cost:
        await update.message.reply_text(f"⚠️ Not enough Credits to upgrade. Cost: {cost}")
        return

    player.credits -= cost
    player.lab_level += 1
    save_player(player)
    # Apply research bonus
    player.research["speed"] += 1
    player.research["armor"] += 1
    save_player(player)
    await update.message.reply_text(f"🔬 Lab upgraded to level {player.lab_level}!")

async def upgrade_defense_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /upgradedefense command."""

    cost = 200 * (player.defense_level + 1)
    if player.ore < cost or player.credits < cost:
        await update.message.reply_text(f"⚠️ Not enough resources to upgrade Defense. Cost: {cost} Ore and Credits")
        return

    player.ore -= cost
    player.credits -= cost
    player.defense_level += 1
    save_player(player)
    await update.message.reply_text(f"🛡️ Defense upgraded to level {player.defense_level}!")

# ===============================
# Main Message Handler (Modified)
# ===============================

COMMAND_HANDLERS = {
    "/start": start_command,
    "/name": name_command,
    "/status": status_command,
    "/daily": daily_command,
    "/mine": mine_command,
    "/forge": forge_command,
    "/use": use_command,
    "/unlockbm": unlockbm_command,
    "/blackmarket": blackmarket_command,
    "/buy": buy_command,
    "/map": map_command,
    "/claim": claim_command,
    "/missions": missions_command,
    "/attack": attack_command,  # Added attack
    "/upgraderefinery": upgrade_refinery_command,
    "/upgradelab": upgrade_lab_command,
    "/upgradedefense": upgrade_defense_command,
    "/help": help_command,
    "/rules": rules_command,
    # ... (Add faction commands in Part 5)
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all incoming messages."""

    if not update.message:
        return

    text = update.message.text.strip()
    cid = update.message.chat_id

    player = find_or_create_player(cid)  # Ensure player exists

    for command, handler in COMMAND_HANDLERS.items():
        if text.startswith(command):
            try:
                await handler(update, context, player)
            except Exception as e:
                print(f"Error handling command {command}: {e}")
                await update.message.reply_text(
                    "⚠️ An error occurred. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            return  # Stop processing after handling the command

    # Handle non-command messages (you can add game logic here if needed)
    # For example, you could check for zone chat or other interactions
    # await update.message.reply_text("💬 I received your message!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Connect all handlers
    for command, handler in COMMAND_HANDLERS.items():
        app.add_handler(CommandHandler(command[1:], handler))  # Remove the leading "/"

    app.run_polling()
What Part 4 Adds:

Attack Command: Implements the /attack command with basic combat logic, shield application, and win/loss tracking.
Building Upgrades: Implements /upgraderefinery, /upgradelab, and /upgradedefense commands, allowing players to upgrade their buildings.
Modified COMMAND_HANDLERS: Includes the new attack and upgrade commands.
Next Steps:

Combine All Parts: Copy the code from Part 4 and paste it after the combined code of Parts 1, 2, and 3.
Test: Run the bot and thoroughly test the attack and upgrade commands. Pay close attention to:
Shield application and expiration.
Resource costs for upgrades.
Combat calculations.
Win/loss tracking.
Are you ready for Part 5, where we'll add faction functionality?


ready for Part 5



Okay, here's Part 5, which adds the faction functionality:

Python

# ===============================
# SkyHustle: HyperClean Part 5
# ===============================

#   (Parts 1, 2, 3, and 4 code goes here - do not repeat it)

# ===============================
# Faction Commands
# ===============================

async def join_faction_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /joinfaction command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("🚩 Usage: /joinfaction <faction_name>")
        return

    faction_name = parts[1].capitalize()
    valid_factions = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]  # Define valid faction names
    if faction_name not in valid_factions:
        await update.message.reply_text(f"❌ Invalid faction. Choose from: {', '.join(valid_factions)}")
        return

    if player.faction:
        await update.message.reply_text(f"🛡️ You are already in the {player.faction} faction.")
        return

    player.faction = faction_name
    save_player(player)
    await update.message.reply_text(f"🤝 Joined the {faction_name} faction!")

async def leave_faction_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /leavefaction command."""

    if not player.faction:
        await update.message.reply_text("🍂 You are not currently in a faction.")
        return

    old_faction = player.faction
    player.faction = None
    save_player(player)
    await update.message.reply_text(f"👋 Left the {old_faction} faction.")

async def faction_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /factioninfo command."""

    if not player.faction:
        await update.message.reply_text("ℹ️ You are not currently in a faction. Use /joinfaction to join one.")
        return

    faction_name = player.faction
    #  Replace this with your actual faction data retrieval (from a dictionary, etc.)
    faction_data = {
        "Aries": {"desc": "The fiery warriors.", "bonus": "+10% attack"},
        "Taurus": {"desc": "The steadfast builders.", "bonus": "+10% defense"},
        "Gemini": {"desc": "The cunning traders.", "bonus": "+10% credits gain"},
        "Cancer": {"desc": "The resilient defenders.", "bonus": "+20% more units after attack"},
        "Leo": {"desc": "The charismatic leaders.", "bonus": "+5% attack, +5% credits gain"},
        "Virgo": {"desc": "The diligent miners.", "bonus": "+20% more ore from mining"},
        "Libra": {"desc": "The balanced diplomats.", "bonus": "+5% attack, +5% defense"},
        "Scorpio": {"desc": "The strategic tacticians.", "bonus": "+10% more units after attack"},
        "Sagittarius": {"desc": "The adventurous explorers.", "bonus": "+10% energy regen"},
        "Capricorn": {"desc": "The disciplined engineers.", "bonus": "-10% cost for upgrades"},
        "Aquarius": {"desc": "The innovative scientists.", "bonus": "+10% research speed"},
        "Pisces": {"desc": "The mystical healers.", "bonus": "+10% defense, +5% energy regen"},
    }

    if faction_name not in faction_data:
        await update.message.reply_text("❌ Faction data not found.")  # Handle potential error
        return

    info = faction_data[faction_name]
    await update.message.reply_text(
        f"🚩 *{faction_name} Faction:*\n{info['desc']}\nBonus: {info['bonus']}",
        parse_mode=ParseMode.MARKDOWN,
    )

# ===============================
# Main Message Handler (Modified)
# ===============================

COMMAND_HANDLERS = {
    "/start": start_command,
    "/name": name_command,
    "/status": status_command,
    "/daily": daily_command,
    "/mine": mine_command,
    "/forge": forge_command,
    "/use": use_command,
    "/unlockbm": unlockbm_command,
    "/blackmarket": blackmarket_command,
    "/buy": buy_command,
    "/map": map_command,
    "/claim": claim_command,
    "/missions": missions_command,
    "/attack": attack_command,
    "/upgraderefinery": upgrade_refinery_command,
    "/upgradelab": upgrade_lab_command,
    "/upgradedefense": upgrade_defense_command,
    "/joinfaction": join_faction_command,  # Added faction commands
    "/leavefaction": leave_faction_command,
    "/factioninfo": faction_info_command,
    "/help": help_command,
    "/rules": rules_command,
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all incoming messages."""

    if not update.message:
        return

    text = update.message.text.strip()
    cid = update.message.chat_id

    player = find_or_create_player(cid)  # Ensure player exists

    for command, handler in COMMAND_HANDLERS.items():
        if text.startswith(command):
            try:
                await handler(update, context, player)
            except Exception as e:
                print(f"Error handling command {command}: {e}")
                await update.message.reply_text(
                    "⚠️ An error occurred. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            return  # Stop processing after handling the command
    # Handle non-command messages (you can add game logic here if needed)
    # For example, you could check for zone chat or other interactions
    # await update.message.reply_text("💬 I received your message!")
# App Main Loop
if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Connect extra /help and /rules commands...
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", rules_command))

    # Connect all handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("name", name_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("mine", mine_command))
    app.add_handler(CommandHandler("forge", forge_command))
    app.add_handler(CommandHandler("use", use_command))
    app.add_handler(CommandHandler("unlockbm", unlockbm_command))
    app.add_handler(CommandHandler("blackmarket", blackmarket_command))
    app.add_handler(CommandHandler("buy", buy_command))

    app.run_polling()
