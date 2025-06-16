
import time
from datetime import date, timedelta
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import init, get_rows, append_row, update_row
from utils.format_utils import section_header

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

    # Helper to find column indices
    def idx(col):
        return header.index(col) if col in header else None

    # Indices
    last_login_idx = idx('last_login')
    streak_idx     = idx('login_streak')
    progress_idx   = idx('progress')
    last_seen_idx  = idx('last_seen')

    today = date.today()
    today_str = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    existing_ids = {r[0] for r in rows[1:]} if len(rows) > 1 else set()

    # ─── New player registration ─────────────────────────────────────────────
    if uid not in existing_ids:
        new_row = [''] * len(header)
        mapping = {
            'user_id':        uid,
            'commander_name': '',
            'username':       user.username or '',
            'credits':       '1000',
            'minerals':      '1000',
            'energy':        '1000',
        }
        for col, val in mapping.items():
            i = idx(col)
            if i is not None:
                new_row[i] = val

        # Initialize tutorial progress to step 1
        if progress_idx is not None:
            new_row[progress_idx] = '1'
        # Initialize login streak and timestamp
        if last_login_idx is not None:
            new_row[last_login_idx] = today_str
        if streak_idx is not None:
            new_row[streak_idx] = '1'

        append_row('Players', new_row)

        # Send step 1 tutorial
        lines = [
            section_header("🌍 Welcome to SkyHustle 🌍"),
            "",
            "The world is in ruins. Ancient powers lie buried beneath the ashes.",
            "Only a true Commander can restore hope.",
            "",
            section_header("🧾 Tutorial Step 1"),
            "`/setname <your_name>` — Choose your unique commander name",
            "",
            "🎁 First Reward: +500 ⚡ Energy"
        ]
        markup = ReplyKeyboardMarkup(
            [[KeyboardButton("/setname YourName")]],
            resize_keyboard=True
        )
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )

    # ─── Existing player login ────────────────────────────────────────────────
    commander_name = None
    reward_msgs = []
    streak = 1

    for ri, row in enumerate(rows[1:], start=1):
        if row[0] != uid:
            continue

        # Ensure row has all columns
        while len(row) < len(header):
            row.append('')

        # Update last_seen timestamp
        if last_seen_idx is not None:
            row[last_seen_idx] = str(int(time.time()))

        # Calculate login streak
        if last_login_idx is not None and streak_idx is not None:
            last_login = row[last_login_idx]
            streak = int(row[streak_idx] or '0')
            if last_login == today_str:
                pass  # already logged in today
            elif last_login == yesterday_str:
                streak += 1
            else:
                streak = 1

            row[last_login_idx] = today_str
            row[streak_idx]     = str(streak)

            # Milestone rewards
            cred_i = idx('credits')
            if streak == 3 and cred_i is not None:
                row[cred_i] = str(int(row[cred_i]) + 100)
                reward_msgs.append("💳 +100 Credits for 3-day streak!")
            elif streak == 7 and cred_i is not None:
                row[cred_i] = str(int(row[cred_i]) + 300)
                reward_msgs.append("💳 +300 Credits for 7-day streak!")
            elif streak == 14 and cred_i is not None:
                row[cred_i] = str(int(row[cred_i]) + 500)
                reward_msgs.append("💳 +500 Credits for 14-day streak!")

        update_row('Players', ri, row)

        cm_i = idx('commander_name')
        commander_name = row[cm_i].strip() if cm_i is not None and row[cm_i] else user.first_name
        break

    # Notify any streak rewards
    for msg in reward_msgs:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # ─── Welcome back UI ──────────────────────────────────────────────────────
    lines = [
        section_header(f"🎖️ Welcome back, Commander {commander_name}!"),
        "",
        f"🔄 Login Streak: *{streak}* day{'s' if streak != 1 else ''}.",
        "",
        "🗒️ Use `/status` to view your base, or `/help` for all commands."
    ]
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 View Base Status", callback_data="status"),
        InlineKeyboardButton("🆘 Help Menu", callback_data="help")
    ]])
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler('start', start)
