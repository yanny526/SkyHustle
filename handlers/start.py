
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

    last_login_idx = idx('last_login')
    streak_idx     = idx('login_streak')
    progress_idx   = idx('progress')

    today       = date.today()
    today_str   = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    existing_ids = {r[0] for r in rows[1:]} if len(rows) > 1 else set()

    # ─── New player registration ─────────────────────────────────────────────
    if uid not in existing_ids:
        # Build a blank row matching the header length
        new_row = [''] * len(header)
        # Core initial values
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
        # Initialize login streak
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
            "
".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )

    # ─── Existing player login ────────────────────────────────────────────────
    # (keep login streak and welcome back behavior unchanged)
    # ...
