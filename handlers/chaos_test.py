# handlers/chaos_test.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from modules.chaos_storms_manager import get_random_storm, apply_storm, record_storm

async def chaos_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos_test – admin-only command to trigger a Chaos Storm immediately.
    """
    user_id = update.effective_user.id
    admins_rows = get_rows("administrators")
    admin_ids = [int(r[0]) for r in admins_rows[1:] if r and r[0].isdigit()]

    if user_id not in admin_ids:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    # Force a random storm
    storm = get_random_storm()
    apply_storm(storm)
    record_storm(storm["id"])

    title = f"{storm['emoji']} *{storm['name']}*"
    text = (
        f"{title}\n\n"
        f"{storm['story']}\n\n"
        "⚠️ This storm was manually triggered by an administrator."
    )

    players = get_rows("Players")
    for row in players[1:]:
        try:
            chat_id = int(row[0])  # chat_id in column A
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            continue

handler = CommandHandler("chaos_test", chaos_test)
