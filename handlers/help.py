# handlers/help.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help – show all commands and usage.
    """
    text = (
        "🆘 *SkyHustle Help*\n\n"
        "/start – Register or welcome back\n"
        "/setname <name> – Pick a unique commander name\n"
        "/menu – Show commands menu\n"
        "/status – View your base status\n"
        "/build <building> – Upgrade a building\n"
        "/queue – List pending upgrades\n"
        "/train <unit> <count> – Train new units\n"
        "/attack <CommanderName> – Attack another commander (5⚡)\n"
        "/leaderboard – See top commanders\n"
        "/help – Show this help message"
    )

    # ✅ Respond to both command or inline
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('help', help_command)
