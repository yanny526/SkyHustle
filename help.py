# handlers/help.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help – show all commands and usage, grouped by category.
    """
    text = "\n".join([
        "🆘 *SkyHustle Help* 🆘",
        "",
        "🛠️ *General*",
        " • `/start` – Register or welcome back",
        " • `/setname <name>` – Pick/change your commander name",
        " • `/help` – Show this help message",
        "",
        "🏰 *Base Management*",
        " • `/status` – View your base status",
        " • `/build <building>` – Upgrade a building",
        " • `/queue` – List pending building upgrades",
        "",
        "⚔️ *Military Operations*",
        " • `/train <unit> <count>` – Train units",
        " • `/attack <Commander> ...` – Launch or cancel attacks/scouts",
        " • `/army` – Show your army breakdown",
        "",
        "💬 *Messaging*",
        " • `/whisper <Commander> <msg>` – Send a private message",
        " • `/inbox` – Read your last 5 whispers",
        "",
        "🏆 *Challenges & Rewards*",
        " • `/daily` – Claim & view daily challenges",
        " • `/weekly` – Claim & view weekly challenges",
        " • `/leaderboard` – See top commanders by power",
        "",
        "🔧 *Profile & Misc*",
        " • `/achievements` – View your achievements",
        " • `/chaos` – View or trigger Chaos Storms",
        "",
        "Use `/help` anytime to revisit this menu!"
    ])

    # Inline button now links to /status
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📊 View Base Status", callback_data="status")
    )

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )

handler = CommandHandler('help', help_command)
