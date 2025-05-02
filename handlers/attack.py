from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

def handler(update: Update, context: CallbackContext):
    update.message.reply_text("/attack not implemented yet.")

handler = CommandHandler('attack', handler)
