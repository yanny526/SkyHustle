# handlers/chaos_test.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from modules.chaos_storms_manager import get_random_storm, apply_storm, record_storm

async def chaos_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos_test – admin-only trigger for immediate Chaos Storm.
    """
    user_id = update.effective_user.id
    admins = [int(r[0]) for r in get_rows("administrators")[1:] if r and r[0].isdigit()]
    if user_id not in admins:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    storm = get_random_storm()
    apply_storm(storm)
    record_storm(storm["id"])

    header = "🚨🔥 *ADMIN-TRIGGERED CHAOS STORM!* 🔥🚨"
    name_line = f"{storm['emoji']} *{storm['name'].upper()}* {storm['emoji']}"
    body = storm['story']
    footer = "🛡️ *Stand ready!* This storm was unleashed by command."

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
            continue

handler = CommandHandler("chaos_test", chaos_test)
