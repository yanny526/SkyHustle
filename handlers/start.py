# handlers/start.py

import time
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import init, get_rows, append_row, update_row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - register a new player if needed, or welcome back existing one.
    """
    # Ensure required sheets and headers exist
    init()

    user = update.effective_user
    rows = get_rows('Players')
    existing_ids = {row[0] for row in rows[1:]} if len(rows) > 1 else set()

    if str(user.id) not in existing_ids:
        # New player: append with blank commander_name
        append_row('Players', [
            str(user.id),
            '',                             # commander_name to be set
            user.username or '',
            '1000',                         # starting credits
            '1000',                         # starting minerals
            '1000',                         # starting energy
            str(int(time.time()))          # last_seen timestamp
        ])
        await update.message.reply_text(
            "🎖️ Welcome, new Commander!\n"
            "❓ First, pick your unique *Commander Name*:\n"
            "`/setname <your_name>`\n"
            "Use letters, numbers, or underscores (no spaces).\n"
            "Example: `/setname IronLegion`",
            parse_mode='Markdown'
        )
    else:
        # Existing player: update last_seen and welcome back
        # find their row index
        for idx, row in enumerate(rows):
            if idx == 0:
                continue
            if row[0] == str(user.id):
                # update last_seen (column 7, zero-based index 6)
                row[6] = str(int(time.time()))
                update_row('Players', idx, row)
                commander_name = row[1] or user.first_name
                break

        await update.message.reply_text(
            f"🎖️ Welcome back, Commander *{commander_name}*!\n"
            "Use /menu to see your commands.",
            parse_mode='Markdown'
        )

handler = CommandHandler('start', start)
