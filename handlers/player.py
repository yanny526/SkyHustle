# handlers/player.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db
import re

# Proper forbidden pattern to block emojis and symbols
FORBIDDEN_PATTERN = re.compile(
    r"["
    "\U00010000-\U0010FFFF"  # Supplementary Multilingual Plane
    "\u2600-\u26FF"          # Misc symbols (Weather etc.)
    "!@#%&*^$?{}[]()/\\<>=+`~"  # Manually forbidden symbols
    "]", flags=re.UNICODE
)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player's current profile."""
    telegram_id = update.effective_user.id
    player = db.get_player_data(telegram_id)

    if not player:
        return await update.message.reply_text("⚠️ You don't have a SkyHustle profile yet! Use /start to create one.")

    text = (
        f"👑 **Commander Profile**\n\n"
        f"👤 Name: {player['PlayerName']}\n"
        f"🌍 Zone: {player['Zone']}\n"
        f"💰 Gold: {player['Gold']}\n"
        f"🪨 Stone: {player['Stone']}\n"
        f"⛓️ Iron: {player['Iron']}\n"
        f"⚡ Energy: {player['Energy']}\n"
        f"🛡️ Shield Active: {player['ShieldActive']}\n"
    )

    await update.message.reply_text(text)

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow a player to set or change their name."""
    telegram_id = update.effective_user.id

    if len(context.args) < 1:
        return await update.message.reply_text("✏️ Usage: /setname <your_new_name>")

    new_name = " ".join(context.args)

    # HARD FILTER: Must only be ASCII letters, numbers, or spaces
    if not new_name.replace(" ", "").isalnum():
        return await update.message.reply_text("🚫 Name must contain only letters, numbers, and spaces. No emojis or special symbols!")

    # SECOND FILTER: Unicode emoji forbidden
    if FORBIDDEN_PATTERN.search(new_name):
        return await update.message.reply_text("🚫 Name contains forbidden characters (emojis, symbols)!")

    # Check if name is already taken
    all_players = db.player_profile.col_values(1)[1:]  # Skip header
    if new_name in all_players:
        return await update.message.reply_text("❌ This name is already taken by another Commander! Choose another.")

    # Update the player's name
    row = db.find_player(telegram_id)
    if not row:
        return await update.message.reply_text("⚠️ You don't have a profile yet! Use /start first!")

    db.player_profile.update_cell(row, 1, new_name)
    await update.message.reply_text(f"✅ Your new Commander name is: **{new_name}**\nLead your empire with honor!")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give daily reward."""
    await update.message.reply_text("🎁 Daily rewards feature coming soon...")
