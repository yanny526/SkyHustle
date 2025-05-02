from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

def handler(update: Update, context: CallbackContext):
    update.message.reply_text("/train not implemented yet.")

handler = CommandHandler('train', handler)
