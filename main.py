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
        return client.open_by_url(SHEET_URL).worksheet("SkyHustle")
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

# ===============================
# Player Class
# ===============================

class Player:
    def __init__(self, chat_id, name="", ore=0, energy=100, credits=100, army=None,
                 zone="", shield_until=None, daily_streak=0, last_daily="",
                 black_market_unlocked=False, items=None, missions=None,
                 last_mission_reset="", wins=0, losses=0, banner="",
                 refinery_level=0, lab_level=0, defense_level=0, research=None,
                 faction=None):
        self.chat_id = chat_id
        self.name = name
        self.ore = ore
        self.energy = energy
        self.credits = credits
        self.army = army if army is not None else {"scout": 0, "tank": 0, "drone": 0}
        self.zone = zone
        self.shield_until = shield_until
        self.daily_streak = daily_streak
        self.last_daily = last_daily
        self.black_market_unlocked = black_market_unlocked
        self.items = items if items is not None else []
        self.missions = missions if missions is not None else {}
        self.last_mission_reset = last_mission_reset
        self.wins = wins
        self.losses = losses
        self.banner = banner
        self.refinery_level = refinery_level
        self.lab_level = lab_level
        self.defense_level = defense_level
        self.research = research if research is not None else {"speed": 0, "armor": 0}
        self.faction = faction

    def to_dict(self):
        """Converts the Player object to a dictionary for storage."""
        return {
            "ChatID": self.chat_id,
            "Name": self.name,
            "Ore": self.ore,
            "Energy": self.energy,
            "Credits": self.credits,
            "Army": json.dumps(self.army),
            "Zone": self.zone,
            "ShieldUntil": self.shield_until,
            "DailyStreak": self.daily_streak,
            "LastDaily": self.last_daily,
            "BlackMarketUnlocked": self.black_market_unlocked,
            "Items": json.dumps(self.items),
            "Missions": json.dumps(self.missions),
            "LastMissionReset": self.last_mission_reset,
            "Wins": self.wins,
            "Losses": self.losses,
            "Banner": self.banner,
            "RefineryLevel": self.refinery_level,
            "LabLevel": self.lab_level,
            "DefenseLevel": self.defense_level,
            "Research": json.dumps(self.research),
            "Faction": self.faction,
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Player object from a dictionary (retrieved from storage)."""
        #  Handle potential JSONDecodeErrors
        try:
            army = json.loads(data.get("Army", '{"scout": 0, "tank": 0, "drone": 0}'))
        except (json.JSONDecodeError, TypeError):
            army = {"scout": 0, "tank": 0, "drone": 0}

        try:
            items = json.loads(data.get("Items", "[]"))
        except (json.JSONDecodeError, TypeError):
            items = []

        try:
            missions = json.loads(data.get("Missions", "{}"))
        except (json.JSONDecodeError, TypeError):
            missions = {}

        try:
            research = json.loads(data.get("Research", "{}"))
        except (json.JSONDecodeError, TypeError):
            research = {}

        return cls(
            chat_id=int(data.get("ChatID", 0)),  # Provide default value
            name=data.get("Name", ""),
            ore=int(data.get("Ore", 0)),
            energy=int(data.get("Energy", 100)),
            credits=int(data.get("Credits", 100)),
            army=army,
            zone=data.get("Zone", ""),
            shield_until=data.get("ShieldUntil", None),
            daily_streak=int(data.get("DailyStreak", 0)),
            last_daily=data.get("LastDaily", ""),
            black_market_unlocked=bool(data.get("BlackMarketUnlocked", False)),
            items=items,
            missions=missions,
            last_mission_reset=data.get("LastMissionReset", ""),
            wins=int(data.get("Wins", 0)),
            losses=int(data.get("Losses", 0)),
            banner=data.get("Banner", ""),
            refinery_level=int(data.get("RefineryLevel", 0)),
            lab_level=int(data.get("LabLevel", 0)),
            defense_level=int(data.get("DefenseLevel", 0)),
            research=research,
            faction=data.get("Faction", None)
        )

# ===============================
# Data Access Functions
# ===============================

def get_all_players(sheet):
    """Fetches all player data from the sheet and returns a list of Player objects."""
    try:
        records = sheet.get_all_records()
        return [Player.from_dict(row) for row in records]
    except Exception as e:
        print(f"Error fetching all players: {e}")
        return []

def find_player_by_chat_id(sheet, chat_id):
    """Finds a player by their chat ID."""
    players = get_all_players(sheet)
    for player in players:
        if player.chat_id == chat_id:
            return player
    return None

def find_player_by_name(sheet, name):
    """Finds a player by their name (alias)."""
    players = get_all_players(sheet)
    for player in players:
        if player.name.lower() == name.lower():
            return player
    return None

def save_player(sheet, player):
    """Saves a player's data back to the Google Sheet."""
    player_data = player.to_dict()
    row_data = [
        player_data.get("ChatID"),
        player_data.get("Name"),
        player_data.get("Ore"),
        player_data.get("Energy"),
        player_data.get("Credits"),
        player_data.get("Army"),
        player_data.get("Zone"),
        player_data.get("ShieldUntil"),
        player_data.get("DailyStreak"),
        player_data.get("LastDaily"),
        player_data.get("BlackMarketUnlocked"),
        player_data.get("Items"),
        player_data.get("Missions"),
        player_data.get("LastMissionReset"),
        player_data.get("Wins"),
        player_data.get("Losses"),
        player_data.get("Banner"),
        player_data.get("RefineryLevel"),
        player_data.get("LabLevel"),
        player_data.get("DefenseLevel"),
        player_data.get("Research"),
        player_data.get("Faction"),
    ]

    try:
        if "_row" in player_data and player_data["_row"]:
            row_number = int(player_data["_row"])
            sheet.update(f"A{row_number}:V{row_number}", [row_data])
        else:
            # Handle new player save (append)
            new_row = row_data
            sheet.append_row(new_row)
            # Update the player's row number after appending (less efficient, but works)
            #  This is tricky, you might need to rethink how you track row numbers
            #  A better approach might be to reload the player after appending
            #  Or to maintain a local cache of row numbers
            #  For now, we'll leave it simple, but be aware of the inefficiency
    except Exception as e:
        print(f"Error saving player {player.name}: {e}")

def create_new_player(sheet, chat_id):
    """Creates a new player in the Google Sheet."""
    new_player = Player(chat_id=chat_id)  # Create a new Player object
    save_player(sheet, new_player)  # Save it to the sheet

    #  Inefficiently retrieve the player with the row number
    #  This is a temporary workaround
    return find_player_by_chat_id(sheet, chat_id)

def find_or_create_player(sheet, chat_id):
    """Finds a player by chat ID, or creates a new one if not found."""
    player = find_player_by_chat_id(sheet, chat_id)
    if not player:
        player = create_new_player(sheet, chat_id)
    return player

# ===============================
# Command Handlers
# ===============================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("⚠️  Error connecting to the game. Please try again later.")
        return

    cid = update.message.chat_id
    player = find_or_create_player(sheet, cid)
    await update.message.reply_text(
        f"🚀 Welcome to SkyHustle, Commander {player.name or 'Unknown'}!\n"
        "Use /help to see available commands."
    )

async def name_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /name command."""
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("⚠️  Error connecting to the game. Please try again later.")
        return

    cid = update.message.chat_id
    player = find_or_create_player(sheet, cid)

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("📛 Usage: /name <alias>")
        return

    new_name = parts[1]
    player.name = new_name
    save_player(sheet, player)
    await update.message.reply_text(f"✅ Your commander alias is now {new_name}.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /status command."""
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("⚠️  Error connecting to the game. Please try again later.")
        return

    cid = update.message.chat_id
    player = find_or_create_player(sheet, cid)

    status_message = f"""
    🌟 Commander: {player.name or 'Unknown'}
    💰 Credits: {player.credits}
    ⛏️ Ore: {player.ore}
    ⚡ Energy: {player.energy}
    ⚔️ Army: {player.army}
    🚩 Zone: {player.zone or 'None'}
    """
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)

async def mine_command(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Handles the /mine command."""
    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("⛏️ Usage: /mine <count>")
        return

    try:
        count = int(parts[1])
    except ValueError:
        await update.message.reply_text("⛏️ Count must be a number.")
        return

    if player.energy < count * 5:
        await update.message.reply_text("⚠️ Not enough energy to mine that much.")
        return

    ore_gain = 20 * count + (player.refinery_level * 5)
    credits_gain = 10 * count
    player.ore += ore_gain
    player.credits += credits_gain
    player.energy -= count * 5
    save_player(player)
    # check_mission_progress(player, "mine", ore_gain)  # Track mission progress
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
    if player.ore < cost_ore * count or player.credits < cost ⚠️ Not enough resources.")
        return

    player.army[unit] += count
    player.ore -= cost_ore * count
    player.credits -= cost_credits * count
    save_player(player)
    await update.message.reply_text(f"⚒️ Forged {count} {unit}(s).")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    help_text = """
    📜 Available Commands:
    /start - Start the game and register your commander.
    /name <alias> - Set your commander's alias.
    /status - Display your commander's status.
    /mine <count> - Mine ore (requires energy).
    /forge <unit> <count> - Forge army units (scout, tank, drone).
    /help - Show this help message.
    """
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles errors."""
    print(f"⚠️ Update {update} caused error {context.error}")

# ===============================
# Main Function - Bot Setup and Running
# ===============================

async def main():
    """Main function - sets up and runs the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("name", name_command))
    application.add_handler(CommandHandler("status", status_command))
    #  We need to use a lambda to pass the player object
    application.add_handler(CommandHandler("mine", lambda update, context: mine_command(update, context, find_or_create_player(get_sheet(), update.message.chat_id))))
    application.add_handler(CommandHandler("forge", lambda update, context: forge_command(update, context, find_or_create_player(get_sheet(), update.message.chat_id))))
    application.add_handler(CommandHandler("help", help_command))

    # Error handler
    application.add_error_handler(error_handler)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
