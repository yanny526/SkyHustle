# handlers/start.py

import time
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import init, get_rows, append_row, update_row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - register a new player or welcome back existing one.
    """
    # Ensure sheets exist
    init()

    user = update.effective_user
    uid = str(user.id)
    rows = get_rows('Players')
    existing_ids = {row[0] for row in rows[1:]} if len(rows) > 1 else set()

    if uid not in existing_ids:
        # New player registration
        append_row('Players', [
            uid,
            '',                             # commander_name
            user.username or '',
            '1000',                         # credits
            '1000',                         # minerals
            '1000',                         # energy
            str(int(time.time()))          # last_seen
        ])

        intro = (
            "🌍 *The world is in ruins.*\n"
            "You are the last hope of your region.\n"
            "Command your base, rebuild power, and rise to dominate.\n\n"
            "🧰 You’ve received a starter pack:\n"
            "💳 1000 Credits\n⛏️ 1000 Minerals\n⚡ 1000 Energy\n\n"
            "📋 *Your first task:*\n"
            "`/build powerplant` – Start generating energy.\n\n"
            "After that, use `/status` to check your base."
        )

        # Quick access buttons
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("/build powerplant")], [KeyboardButton("/status")]],
            resize_keyboard=True
        )

        await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    else:
        # Existing player logic
        for idx, row in enumerate(rows):
            if idx == 0:
                continue
            if row[0] == uid:
                row[6] = str(int(time.time()))
                update_row('Players', idx, row)
                commander_name = row[1] or user.first_name
                break

        await update.message.reply_text(
            f"🎖️ Welcome back, Commander *{commander_name}*!\n"
            "Use /menu or /status to continue.",
            parse_mode=ParseMode.MARKDOWN
        )

handler = CommandHandler('start', start)
