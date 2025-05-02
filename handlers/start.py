from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import init, get_rows, append_row, update_row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name

    # make sure a player record exists
    rows = get_rows("Players")[1:]  # skip header
    for i, row in enumerate(rows, start=2):
        if str(row[0]) == str(uid):
            await update.message.reply_text(f"Welcome back, {username}!")
            return

    # new player → append initial
    append_row("Players", [uid, username, 1000, 0, 0, 0, 0])
    await update.message.reply_text(
        f"Hello, {username}! 🎉\n"
        "You’ve been given 1,000 minerals to get started. 
Use /menu to see what you can do."
    )

handler = CommandHandler("start", start)
