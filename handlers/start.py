from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    created = db.create_player(user.id, user.first_name)
    
    if created:
        await update.message.reply_text(
            "🌌 **Welcome, Commander!** 🌌\n\n"
            "A new empire is born from the ashes...\n"
            "Type /help to begin your conquest! 🏰"
        )
    else:
        await update.message.reply_text(
            "🏰 **Welcome back, Commander!**\n\n"
            "Your empire awaits your command. ⚔️"
        )
