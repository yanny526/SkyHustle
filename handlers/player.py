# handlers/player.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db
import utils.validation as validation  # Make sure this is created!

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player's current profile."""
    telegram_id = update.effective_user.id
    player = db.get_player_data(telegram_id)

    if not player:
        return await update.message.reply_text("⚠️ You don't have a SkyHustle profile yet! Use /start to create one.")

    text = (
        f"👑 **Commander Profile** \n\n"
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

    # Check if name is valid
    if not validation.is_valid_name(new_name):
        return await update.message.reply_text("🚫 Name must only contain letters, numbers, and spaces (no emojis or symbols)!")

    # Check if name is already taken
    all_players = db.player_profile.col_values(1)[1:]  # Skip header
    if new_name in all_players:
        return await update.message.reply_text("❌ This name is already taken by another Commander!")

    # Update the name
    row = db.find_player(telegram_id)
    if not row:
        return await update.message.reply_text("⚠️ You don't have a profile yet! Use /start first!")

    db.player_profile.update_cell(row, 1, new_name)

    await update.message.reply_text(f"✅ Name successfully changed to: **{new_name}**\nMake your mark, Commander!")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give daily reward."""
    await update.message.reply_text("🎁 Daily rewards feature coming soon...")
