# handlers/chaos_event.py

from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from modules.chaos_storms_manager import trigger_storm
from sheets_service import get_rows

async def chaos_event_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Weekly job to trigger and broadcast a Chaos Storm for all commanders.
    """
    storm = trigger_storm()
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

    players = get_rows("Players")
    for row in players[1:]:
        try:
            chat_id = int(row[0])
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            # consider logging invalid chat_ids here
            continue
