# handlers/menu.py

from telegram import Update, ParseMode
from telegram.ext import CommandHandler, ContextTypes

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /menu - show list of available commands with emojis.
    """
    text = (
        "🗺️ *Available Commands* 🗺️\n\n"
        "🔹 `/status` – View your base status\n"
        "🔹 `/build <building>` – Start or queue an upgrade\n"
        "🔹 `/queue` – Show pending upgrades\n"
        "🔹 `/train <unit> <count>` – Train new units\n"
        "🔹 `/attack <user_id>` – Raid another commander\n"
        "🔹 `/leaderboard` – See top commanders\n"
        "\n"
        "❓ Use `/status` first to see your starting resources!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('menu', menu)
