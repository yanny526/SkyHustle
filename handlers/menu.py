from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

def handler(update: Update, context: CallbackContext):
    text = (
        "🔹 /status - Base status\n"
        "🔹 /build <building> - Upgrade/build\n"
        "🔹 /queue - Pending upgrades\n"
        "🔹 /train <unit> <count> - Train units\n"
        "🔹 /attack <user_id> - Attack player\n"
        "🔹 /leaderboard - Top players"
    )
    update.message.reply_text(text)

handler = CommandHandler('menu', handler)
