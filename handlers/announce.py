# handlers/announce.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from modules.admin_manager import is_admin
from sheets_service import get_rows

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /announce <message> — broadcast to all players.
    Only users listed in the 'Administrators' sheet may run this.
    """
    uid = str(update.effective_user.id)
    # permission check
    if not is_admin(uid):
        return await update.message.reply_text("❌ You are not authorized to use this command.")

    # get announcement text
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        return await update.message.reply_text("❗ Usage: `/announce <your message>`")

    # gather all player IDs
    players = get_rows("Players")
    user_ids = [row[0] for row in players[1:] if row and row[0]]

    # broadcast
    success, failed = 0, 0
    for pid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(pid), text=text)
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📣 Announcement sent to {success} players."
        + (f" {failed} failed." if failed else "")
    )

handler = CommandHandler("announce", announce)

