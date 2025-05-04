# handlers/chaos_event.py

from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from modules.chaos_storms_manager import trigger_storm
from sheets_service import get_rows

async def chaos_event_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Weekly job to trigger a Chaos Storm for all commanders.
    """
    # Attempt to pick & apply a storm
    storm = trigger_storm()
    if not storm:
        # Either already triggered within 7 days or error – do nothing
        return

    # Build the broadcast text
    title = f"{storm['emoji']} *{storm['name']}*"
    text = (
        f"{title}\n\n"
        f"{storm['story']}\n\n"
        "⚠️ These storms strike randomly once a week—brace yourself!"
    )

    # Send to every player by chat_id (assumes chat_id is in column 1 of the Players sheet)
    players = get_rows("Players")
    for row in players[1:]:
        try:
            chat_id = int(row[1])
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            # skip rows with invalid/missing chat_id
            continue
