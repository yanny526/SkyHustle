from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from modules.chaos_storms_manager import get_random_storm, apply_storm
from sheets_service import get_rows

async def chaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos – trigger a random Chaos Storm for all commanders.
    Selects one event, applies its effects to every player,
    and broadcasts the vivid storm story to each of them.
    """
    storm = get_random_storm()
    apply_storm(storm)

    title = f"{storm['emoji']} *{storm['name']}*"
    body = (
        f"{storm['story']}\n\n"
        "⚠️ These storms strike randomly once a week, so brace yourself for the next one!"
    )
    message = f"{title}\n\n{body}"

    # Broadcast to every registered player
    players = get_rows('Players')
    for row in players[1:]:
        try:
            await context.bot.send_message(
                chat_id=int(row[0]),
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            # if a DM fails (e.g. user blocked bot), we skip
            continue

    # Confirm to the admin who invoked it
    await update.message.reply_text(
        f"✅ *{storm['name']}* has struck—everyone has been notified!",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler('chaos', chaos)
