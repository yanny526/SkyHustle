# ===============================
# SkyHustle: HyperClean Part 1
# ===============================

import os
import json
import base64
import asyncio
from datetime import datetime, timedelta, date
import random  # Added in Part 2, but included here for clarity

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
# End of Part 1
# ===============================

#  PASTE PART 2 CODE DIRECTLY BELOW THIS LINE
await update.message.reply_text(f"🏭 Forged {count} {unit}(s). Remaining Ore: {player.ore}, Credits: {player.credits}, Army: {player.army}")

async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /use command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("📦 Usage: /use <item>")
        return

    item = parts[1]
    if item in player.items:
        if item == "shield":
            player.shield_until = (datetime.now() + timedelta(hours=1)).isoformat()
            player.items.remove(item)
            await update.message.reply_text("🛡️ Shield activated for 1 hour.")
        # Add other item effects here
        save_player(player)
    else:
        await update.message.reply_text("📦 You don't have that item.")

async def unlockbm_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /unlockbm command."""

    if player.black_market_unlocked:
        await update.message.reply_text("🔓 Black Market is already unlocked.")
        return

    if player.credits >= 200:
        player.credits -= 200
        player.black_market_unlocked = True
        save_player(player)
        await update.message.reply_text("🔓 Black Market unlocked for 200 Credits.")
    else:
        await update.message.reply_text("⚠️ Not enough Credits to unlock the Black Market (200 needed).")

async def blackmarket_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /blackmarket command."""

    if not player.black_market_unlocked:
        await update.message.reply_text("🔒 Black Market is locked. Use /unlockbm to access.")
        return

    bm_items = {
        "infinityscout": "Gain 5 scouts - 100 Credits",
        "reviveall": "Revive all units to 5 - 500 Credits",
        "hazmat": "Increase ore mining yield - 250 Credits",
        "shield": "Gain a 1-hour shield - 300 Credits"
    }
    message = "⚫ Black Market Items:\n"
    for item, desc in bm_items.items():
        message += f"- {item}: {desc}\n"
    message += "Use /buy <item> to purchase."
    await update.message.reply_text(message)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /buy command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("🛒 Usage: /buy <item>")
        return

    item = parts[1]
    prices = {"infinityscout": 100, "reviveall": 500, "hazmat": 250, "shield": 300}
    effect = {"infinityscout": "scout", "reviveall": "all", "hazmat": "mining", "shield": "shield"}

    price = prices.get(item, 0)
    if price == 0:
        await update.message.reply_text("🛒 Item not found in the Black Market.")
        return

    if not player.black_market_unlocked:
        await update.message.reply_text("🔒 Black Market is locked. Use /unlockbm to access.")
        return

    if player.credits >= price:
        player.credits -= price
        if effect[item] == "scout":
            player.army["scout"] = player.army.get("scout", 0) + 5
            await update.message.reply_text("✅ 5 Scouts added to your army.")
        elif effect[item] == "all":
            for unit in player.army:
                player.army[unit] = 5
            await update.message.reply_text("✅ All units revived to 5.")
        elif effect[item] == "mining":
            player.refinery_level += 1
            await update.message.reply_text("✅ Ore mining yield increased.")
        elif effect[item] == "shield":
            player.items.append("shield")
            await update.message.reply_text("✅ Shield added to your inventory. Use /use shield to activate.")
        save_player(player)
    else:
        await update.message.reply_text(f"⚠️ Not enough Credits to buy {item} ({price} needed).")

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /claim command."""

    text = update.message.text
    parts = text.split()
    if len(parts) != 2 or parts[1] not in enabled_zones:
        await update.message.reply_text(f"🚩 Usage: /claim <zone> (Available zones: {', '.join(enabled_zones)})")
        return

    zone = parts[1]
    owner = find_zone_owner(zone)
    if owner:
        await update.message.reply_text(f"🚩 {zone} is already claimed by {owner.name}.")
        return

    if player.zone:
        old_zone = player.zone
        player.zone = ""
        save_player(player)
        zones[old_zone] = None  # Free the old zone
        await update.message.reply_text(f"🏳️ You abandoned {old_zone}.")

    player.zone = zone
    save_player(player)
    zones[zone] = player.chat_id
    await update.message.reply_text(f"🚩 You have claimed {zone}!")

async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /map command."""

    map_str = "🗺️ Zone Control:\n"
    for zone, owner_id in zones.items():
        owner = find_player_by_chat_id(owner_id)
        owner_name = owner.name if owner else "Unclaimed"
        map_str += f"- {zone}: {owner_name}\n"
    await update.message.reply_text(map_str)

async def missions_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /missions command."""

    today = date.today()
    if player.last_mission_reset != str(today):
        reset_missions(player)

    mission_list = "📜 Daily Missions:\n"
    mission_list += f"- Mine 5 Ore: {'✅' if player.missions.get('mine5') else '⬜'}\n"
    mission_list += f"- Win 1 Battle: {'✅' if player.missions.get('win1') else '⬜'}\n"
    mission_list += f"- Forge 5 Units: {'✅' if player.missions.get('forge5') else '⬜'}\n"
    mission_list += "\nComplete missions for extra rewards!"
    await update.message.reply_text(mission_list)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""

    help_text = """
    🚀 Available Commands:
    /start - Begin your galactic journey
    /name <alias> - Set your commander's alias
    /status - View your current status
    /daily - Claim your daily resources
    /mine ore <count> - Mine for precious ore
    /forge <unit> <count> - Construct army units (scout, tank, drone)
    /use <item> - Use an item from your inventory
    /unlockbm - Unlock the Black Market
    /blackmarket - Browse the Black Market
    /buy <item> - Purchase items from the Black Market
    /attack <player_name> - Engage another commander in battle
    /claim <zone> - Claim a strategic zone
    /map - Display the current zone control
    /missions - View your daily missions
    /help - Show this help message
    /rules - Display the game rules
    """
    await update.message.reply_text(help_text)

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /rules command."""

    rules_text = """
    📜 Galactic Rules of Engagement:
    1. Respect all commanders.
    2. No exploiting bugs or cheats.
    3. Zone control is determined by the last commander to claim it.
    4. Attacks have consequences - be strategic!
    5. Daily rewards are available once per day.
    """
    await update.message.reply_text(rules_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all incoming messages."""

    if not update.message:
        return  # Ignore updates without messages

    cid = update.message.chat_id
    text = update.message.text.strip()
    try:
        player = find_or_create_player(cid)  # Ensure player exists for every message
    except Exception as e:
        print(f"Error finding or creating player for {cid}: {e}")
        await update.message.reply_text(
            "⚠️ An error occurred. Please try again later.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Command Parsing and Handling
    if text.startswith("/start"):
        await start_command(update, context, player)
    elif text.startswith("/name"):
        await name_command(update, context, player)
    elif text.startswith("/status"):
        await status_command(update, context, player)
    elif text.startswith("/daily"):
        await daily_command(update, context, player)
    elif text.startswith("/mine"):
        await mine_command(update, context, player)
    elif text.startswith("/forge"):
        await forge_command(update, context, player)
    elif text.startswith("/use"):
        await use_command(update, context, player)
    elif text.startswith("/unlockbm"):
        await unlockbm_command(update, context, player)
    elif text.startswith("/blackmarket"):
        await blackmarket_command(update, context, player)
    elif text.startswith("/buy"):
        await buy_command(update, context, player)
    elif text.startswith("/attack"):
        await attack_command(update, context, player)  # <---- THIS LINE IS CRUCIAL
    elif text.startswith("/claim"):
        await claim_command(update, context, player)
    elif text.startswith("/map"):
        await map_command(update, context)
    elif text.startswith("/missions"):
        await missions_command(update, context, player)
    elif text.startswith("/help"):
        await help_command(update, context)
    elif text.startswith("/rules"):
        await rules_command(update, context)
    else:
        # Handle non-command messages (e.g., chat, interactions) if needed
        #  await update.message.reply_text("💬 I received your message!")
        pass

async def main():
    """Starts the bot."""

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("name", name_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("mine", mine_command))
    application.add_handler(CommandHandler("forge", forge_command))
    application.add_handler(CommandHandler("use", use_command))
    application.add_handler(CommandHandler("unlockbm", unlockbm_command))
    application.add_handler(CommandHandler("blackmarket", blackmarket_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("attack", attack_command))
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CommandHandler("map", map_command))
    application.add_handler(CommandHandler("missions", missions_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", rules_command))

    # Start the Bot
    print("Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
# ===============================
# SkyHustle: HyperClean Part 2
# ===============================

#   (Part 1 code should already be here)

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
