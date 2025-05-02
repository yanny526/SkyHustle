from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from sheets_service import init, append_row, get_rows
import time

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    users = get_rows('Players')
    ids = [row[0] for row in users[1:]] if len(users) > 1 else []
    if str(user.id) not in ids:
        append_row('Players', [user.id, user.username, 1000, 1000, 1000, int(time.time())])
    update.message.reply_text(
        f"Welcome, Commander {user.first_name}! Use /menu to see commands."
    )

handler = CommandHandler('start', start)
