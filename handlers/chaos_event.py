# handlers/chaos_event.py

from telegram import ParseMode
from telegram.ext import ContextTypes
from modules.chaos_storms_manager import pick_random_storm, apply_storm_to_all
from sheets_service import get_rows

async def chaos_event_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Job that runs weekly: picks a storm, applies it to everyone,
    logs it, and notifies each player.
    """
    storm, delta = apply_storm_to_all(pick_random_storm())
    ts = storm["emoji"]
    title = storm["title"]
    story = storm["story"]

    # Send to every registered player
    players = get_rows("Players")[1:]
    for row in players:
        uid = int(row[0])
        text = (
            f"{storm['emoji']} *Random Chaos Storm!* {storm['emoji']}\n\n"
            f"*{title}*\n"
            f"{story}\n\n"
            f"_(These storms strike randomly once a week – brace yourself!)_"
        )
        await context.bot.send_message(chat_id=uid, text=text, parse_mode=ParseMode.MARKDOWN)
