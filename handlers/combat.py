from telegram import Update
from telegram.ext import ContextTypes

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **Battle Report!** ⚔️\n\n"
        "You launched a daring raid against a rival!\n"
        "🏴‍☠️ Casualties: 5 Soldiers lost.\n"
        "💰 Resources captured: +150 Gold\n\n"
        "Victory is yours, Commander! 🏆"
    )
