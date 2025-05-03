# handlers/menu.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /menu - display the SkyHustle command menu with inline shortcuts
    """
    # Full command list (text-based)
    text = (
        "📜 *SkyHustle Command Menu*\n\n"
        "🛠️ *General*\n"
        " • /start – Register or welcome back\n"
        " • /help – Show help and command list\n"
        " • /menu – Display this menu\n\n"
        "🏰 *Base Management*\n"
        " • /status – View your base status\n"
        " • /build <building> – Upgrade a building (mine, powerplant, barracks, workshop)\n"
        " • /queue – List pending building upgrades\n\n"
        "⚔️ *Military Operations*\n"
        " • /train <unit> <count> – Train units (infantry, tanks, artillery)\n"
        " • /attack <CommanderName> – Attack another commander (costs 5⚡)\n"
        " • /leaderboard – See top commanders by power\n\n"
        "🔧 *Profile*\n"
        " • /setname <name> – Set your unique commander name"
    )

    # Inline quick-action menu
    keyboard = [
        [InlineKeyboardButton("🛡️ Army", callback_data="menu_army")],
        [InlineKeyboardButton("📊 Status", callback_data="menu_status")],
        [InlineKeyboardButton("⏳ Queue", callback_data="menu_queue")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

handler = CommandHandler("menu", menu)
