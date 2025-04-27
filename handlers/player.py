# handlers/player.py
from telegram import Update
from telegram.ext import ContextTypes

from utils.google_sheets import find_or_create_player, save_player, get_sheet
from core.player import Player


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""

    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("⚠️  Error connecting to the game. Please try again later.")
        return

    cid = update.message.chat_id
    player = find_or_create_player(sheet, cid)  # Use the sheet object
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
    player = find_or_create_player(sheet, cid)  # Use the sheet object

    text = update.message.text
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("📛 Usage: /name <alias>")
        return

    new_name = parts[1]
    player.name = new_name
    save_player(sheet, player)  # Use the sheet object
    await update.message.reply_text(f"✅ Your commander alias is now {new_name}.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /status command."""

    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("⚠️  Error connecting to the game. Please try again later.")
        return

    cid = update.message.chat_id
    player = find_or_create_player(sheet, cid)  # Use the sheet object

    status_message = f"""
    🌟 Commander: {player.name or 'Unknown'}
    💰 Credits: {player.credits}
    ⛏️ Ore: {player.ore}
    ⚡ Energy: {player.energy}
    ⚔️ Army: {player.army}
    🚩 Zone: {player.zone or 'None'}
    """
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
