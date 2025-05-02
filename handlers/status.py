from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import time
from sheets_service import get_rows, update_row

def handler(update: Update, context: CallbackContext):
    user = update.effective_user
    # Placeholder: Fetch and calculate status
    update.message.reply_text("Status feature coming soon!")

handler = CommandHandler('status', handler)
