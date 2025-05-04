# handlers/announce.py

from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from modules.admin_manager import is_admin
from sheets_service import get_rows, append_row

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /announce <message> — broadcast to all players.
    Only users listed in the 'Administrators' sheet may run this.
    Logs each announcement (admin user_id, timestamp, message) to the same sheet.
    """
    uid = str(update.effective_user.id)
    # 1) Permission check
    if not is_admin(uid):
        return await update.message.reply_text("❌ You are not authorized to use this command.")
    
    # 2) Extract announcement text
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        return await update.message.reply_text("❗ Usage: `/announce <your message>`")
    
    # 3) Broadcast to all players
    players = get_rows("Players")
    user_ids = [row[0] for row in players[1:] if row and row[0]]
    success, failed = 0, 0
    for pid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(pid), text=text)
            success += 1
        except Exception:
            failed += 1
    
    # 4) Log the announcement in the Administrators sheet
    timestamp = datetime.utcnow().isoformat()
    append_row("Administrators", [uid, timestamp, text])
    
    # 5) Notify the admin of result
    result_msg = f"📣 Announcement sent to {success} players."
    if failed:
        result_msg += f" {failed} failed."
    await update.message.reply_text(result_msg)

handler = CommandHandler("announce", announce)
