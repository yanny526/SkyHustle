# handlers/start.py

import time
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import init, get_rows, append_row, update_row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - register new players or welcome back existing ones,
    and kick off the first quest step.
    """
    init()

    user = update.effective_user
    uid = str(user.id)
    rows = get_rows('Players')
    existing_ids = {r[0] for r in rows[1:]} if len(rows) > 1 else set()

    if uid not in existing_ids:
        # New registration
        append_row('Players', [
            uid,
            '',                             # commander_name
            user.username or '',
            '1000',                         # credits
            '1000',                         # minerals
            '1000',                         # energy
            str(int(time.time())),         # last_seen
            ''                              # progress
        ])

        # 1) Short captivating story
        text = (
            "🌍 *The world is in ruins.*\n"
            "Ancient powers lie buried beneath the ashes.\n"
            "Only a true Commander can restore hope.\n\n"
            "🧾 *Your first task:*\n"
            "`/setname <your_name>` – Choose your unique commander name.\n\n"
            "🎁 *On first completion you’ll earn:* +500 ⚡ Energy\n"
        )

        # offer a quick button to /setname
        markup = ReplyKeyboardMarkup(
            [[KeyboardButton("/setname YourName")]],
            resize_keyboard=True
        )

        return await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    # existing player
    for idx, row in enumerate(rows):
        if idx == 0: continue
        if row[0] == uid:
            row[6] = str(int(time.time()))
            update_row('Players', idx, row)
            commander_name = row[1].strip() or user.first_name
            break

    msg = f"🎖️ Welcome back, Commander *{commander_name}*!\nUse /menu or /status to continue."
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('start', start)
