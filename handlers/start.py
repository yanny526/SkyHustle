# handlers/start.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import init, get_rows, append_row, update_row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - register a new player or welcome back existing one.
    """
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

        await update.message.reply_text(
            "🌍 *The world is in ruins.*\n"
            "You are the last hope of your region.\n"
            "Command your base, rebuild power, and rise to dominate.\n\n"
            "🧰 You’ve received a starter pack:\n"
            "💳 1000 Credits\n⛏️ 1000 Minerals\n⚡ 1000 Energy\n\n"
            "🧾 *Before you begin:*\n"
            "Choose a unique commander name using:\n"
            "`/setname <your_name>`\n\n"
            "_Example: `/setname IronLegion`_",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Existing player: update last_seen
    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        if row[0] == uid:
            row[6] = str(int(time.time()))
            update_row('Players', idx, row)
            commander_name = row[1].strip() or user.first_name
            break

    msg = f"🎖️ Welcome back, Commander *{commander_name}*!\nUse /menu or /status to continue."

    if not commander_name or commander_name.lower() in ["commander", "leader", user.username.lower() if user.username else ""]:
        msg += "\n\n⚠️ Tip: Choose a unique name using `/setname <your_name>` to stand out."

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('start', start)
