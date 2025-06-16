# handlers/chaos_event.py

from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.chaos_engine import engine
from sheets_service import get_rows

async def chaos_event_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Weekly job to trigger and broadcast a Chaos Storm for all commanders.
    """
    storm = engine.trigger_storm()
    if not storm:
        return

    header = "🌪️🌩️ *CHAOS STORM INCOMING!* 🌩️🌪️"
    name_line = f"{storm['emoji']} *{storm['name'].upper()}* {storm['emoji']}"
    body = storm['story']
    footer = "⚠️ *Brace yourselves!* The elements have been unleashed."

    text = (
        f"{header}\n\n"
        f"{name_line}\n\n"
        f"{body}\n\n"
        f"{footer}"
    )

    # Inline button to check status
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔍 Check Status", callback_data="status")
    )

    try:
        players = get_rows("Players")
    except Exception:
        return

    for row in players[1:]:
        try:
            chat_id = int(row[0])  # user_id in col A
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb,
            )
        except Exception:
            continue

def register_event_job(application):
    """
    Schedule chaos_event_job to run weekly at Monday 09:00 UTC.
    Call this in main.py after initializing the application.
    """
    # Calculate next Monday 09:00 UTC
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    days_ahead = (0 - now.weekday() + 7) % 7  # 0 = Monday
    next_monday = now + timedelta(days=days_ahead)
    next_run = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)

    application.job_queue.run_repeating(
        chaos_event_job,
        interval=7 * 24 * 3600,  # weekly
        first=(next_run - now).total_seconds()
    )
