# handlers/start.py

import time
from datetime import date, timedelta
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import init, get_rows, append_row, update_row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - register new players or welcome back existing ones,
    handle daily login streaks and rewards, and kick off the first quest step.
    """
    init()

    user = update.effective_user
    uid = str(user.id)
    rows = get_rows('Players')
    header = rows[0]
    existing_ids = {r[0] for r in rows[1:]} if len(rows) > 1 else set()

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    # New player registration
    if uid not in existing_ids:
        # Build new row with proper columns (pad to header length)
        new_row = [
            uid,
            '',                           # commander_name
            user.username or '',         # username
            '1000',                       # credits
            '1000',                       # minerals
            '1000',                       # energy
            str(int(time.time())),       # last_seen timestamp
            '',                           # progress
            today_str,                    # last_login date
            '1',                          # login_streak
        ]
        # Pad to header length if needed
        while len(new_row) < len(header):
            new_row.append('')
        append_row('Players', new_row)

        # Intro and first task prompt
        text = (
            "🌍 *The world is in ruins.*\n"
            "Ancient powers lie buried beneath the ashes.\n"
            "Only a true Commander can restore hope.\n\n"
            "🧾 *Your first task:*\n"
            "`/setname <your_name>` – Choose your unique commander name.\n\n"
            "🎁 *On first completion you’ll earn:* +500 ⚡ Energy"
        )
        markup = ReplyKeyboardMarkup(
            [[KeyboardButton("/setname YourName")]],
            resize_keyboard=True
        )
        return await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup
        )

    # Existing player: update last_seen, login streak, and rewards
    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        if row[0] == uid:
            # Ensure row has all columns
            while len(row) < len(header):
                row.append('')

            # Update last_seen timestamp
            row[6] = str(int(time.time()))

            # Determine streak
            last_login = row[8]
            streak = int(row[9] or '0')
            if last_login == today_str:
                # already logged in today
                pass
            elif last_login == yesterday_str:
                streak += 1
            else:
                streak = 1

            # Update login info
            row[8] = today_str
            row[9] = str(streak)

            # Award streak rewards at milestones
            reward_msgs = []
            # Example milestones: 3, 7, 14 days
            if streak == 3:
                row[3] = str(int(row[3]) + 100)  # +100 credits
                reward_msgs.append("💳 +100 Credits for a 3-day streak!")
            elif streak == 7:
                row[3] = str(int(row[3]) + 300)  # +300 credits
                reward_msgs.append("💳 +300 Credits for a 7-day streak!")
            elif streak == 14:
                row[3] = str(int(row[3]) + 500)  # +500 credits
                reward_msgs.append("💳 +500 Credits for a 14-day streak!")

            # Persist changes
            update_row('Players', idx, row)

            # Send streak notification if any
            if reward_msgs:
                await update.message.reply_text(
                    f"🎉 Login Streak: {streak} days!\n" + "\n".join(reward_msgs),
                    parse_mode=ParseMode.MARKDOWN
                )

            commander_name = row[1].strip() or user.first_name
            break

    # Welcome back message with streak info
    msg = (
        f"🎖️ Welcome back, Commander *{commander_name}*!
"
        f"🔄 Login Streak: {streak} day{'s' if streak != 1 else ''}.
"
        "Use /menu or /status to continue."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)(msg, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('start', start)
