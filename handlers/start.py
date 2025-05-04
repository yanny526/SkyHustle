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

    # Determine column indices dynamically
    def idx(col):
        return header.index(col) if col in header else None
    last_login_idx = idx('last_login')
    streak_idx = idx('login_streak')
    progress_idx = idx('progress')

    today = date.today()
    today_str = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    existing_ids = {r[0] for r in rows[1:]} if len(rows) > 1 else set()

    # New player registration
    if uid not in existing_ids:
        # Build a blank row of correct length
        new_row = [''] * len(header)
        # Fill core fields by header name
        mapping = {
            'user_id': uid,
            'commander_name': '',
            'username': user.username or '',
            'credits': '1000',
            'minerals': '1000',
            'energy': '1000',
            'last_seen': str(int(time.time())),
        }
        for col, val in mapping.items():
            i = idx(col)
            if i is not None:
                new_row[i] = val
        # progress, last_login, login_streak
        if progress_idx is not None:
            new_row[progress_idx] = ''
        if last_login_idx is not None:
            new_row[last_login_idx] = today_str
        if streak_idx is not None:
            new_row[streak_idx] = '1'
        append_row('Players', new_row)

        # Intro and first task
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

    # Existing player: update fields
    commander_name = None
    for idx_row, row in enumerate(rows):
        if idx_row == 0:
            continue
        if row[0] == uid:
            # ensure row list covers all header columns
            while len(row) < len(header):
                row.append('')
            # update last_seen timestamp
            ls_idx = idx('last_seen')
            if ls_idx is not None:
                row[ls_idx] = str(int(time.time()))
            # get and update login streak columns
            if last_login_idx is not None and streak_idx is not None:
                last_login = row[last_login_idx]
                streak = int(row[streak_idx] or '0')
                if last_login == today_str:
                    # already checked in today
                    pass
                elif last_login == yesterday_str:
                    streak += 1
                else:
                    streak = 1
                row[last_login_idx] = today_str
                row[streak_idx] = str(streak)
                # milestone rewards
                reward_msgs = []
                if streak == 3:
                    cred_i = idx('credits')
                    if cred_i is not None:
                        row[cred_i] = str(int(row[cred_i]) + 100)
                    reward_msgs.append("💳 +100 Credits for 3-day streak!")
                elif streak == 7:
                    cred_i = idx('credits')
                    if cred_i is not None:
                        row[cred_i] = str(int(row[cred_i]) + 300)
                    reward_msgs.append("💳 +300 Credits for 7-day streak!")
                elif streak == 14:
                    cred_i = idx('credits')
                    if cred_i is not None:
                        row[cred_i] = str(int(row[cred_i]) + 500)
                    reward_msgs.append("💳 +500 Credits for 14-day streak!")
                # persist and notify
                update_row('Players', idx_row, row)
                if reward_msgs:
                    await update.message.reply_text(
                        f"🎉 Login Streak: {streak} days!\n" + "\n".join(reward_msgs),
                        parse_mode=ParseMode.MARKDOWN
                    )
            # set commander name for welcome back
            cm_idx = idx('commander_name')
            commander_name = row[cm_idx].strip() if cm_idx is not None else row[1].strip()
            break

    # Welcome back with streak info
    # fallback streak if not updated above
    streak = 1
    if streak_idx is not None and commander_name is not None:
        streak = int(row[streak_idx] or '1')
    msg = (
        f"🎖️ Welcome back, Commander *{commander_name}*!\n"
        f"🔄 Login Streak: {streak} day{'s' if streak != 1 else ''}.\n"
        "Use /menu or /status to continue."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('start', start)
