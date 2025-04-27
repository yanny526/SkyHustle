# handlers/player.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db
import re

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    player = db.get_player_data(telegram_id)
    if not player:
        return await update.message.reply_text("🛡️ You don't have an account yet. Use /start first!")

    text = (
        f"🏰 **Commander Status** 🏰\n\n"
        f"👤 Name: {player['PlayerName']}\n"
        f"💰 Gold: {player['Gold']}\n"
        f"🪨 Stone: {player['Stone']}\n"
        f"⛓️ Iron: {player['Iron']}\n"
        f"⚡ Energy: {player['Energy']}\n"
        f"🛡️ Shield: {player['ShieldActive']}\n"
        f"🌍 Zone: {player['Zone']}"
    )

    await update.message.reply_text(text)

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow a player to set their commander name once."""
    telegram_id = update.effective_user.id

    if len(context.args) != 1:
        return await update.message.reply_text("🖋️ Usage: /setname <yourname>")

    desired_name = context.args[0]

    # Check if player already has a name
    player = db.get_player_data(telegram_id)
    if not player:
        return await update.message.reply_text("🛡️ You don't have an account yet. Use /start first!")

    if player['PlayerName'] != "":
        return await update.message.reply_text("⚠️ You already have a Commander name set. It cannot be changed!")

    # Check if name has emojis (ban them)
    if contains_emoji(desired_name):
        return await update.message.reply_text("❌ Emojis are not allowed in Commander names!")

    # Check if name is unique
    if db.is_name_taken(desired_name):
        return await update.message.reply_text("🚫 This Commander name is already taken. Choose another!")

    # Update player profile
    db.set_player_name(telegram_id, desired_name)
    await update.message.reply_text(f"🏰 Welcome, Commander {desired_name}! Lead your empire to glory! ⚔️")

def contains_emoji(text):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags
                           u"\U00002700-\U000027BF"  # Dingbats
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    return bool(emoji_pattern.search(text))
