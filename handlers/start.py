from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌌 **Welcome, Commander!** 🌌\n\n"
        "After the Great Collapse, the world lies in ruins...\n"
        "From these ashes, YOU shall rise! 🏰\n\n"
        "⚡ Build your empire.\n"
        "⚔️ Conquer the lands.\n"
        "👑 Become the Supreme Ruler of SkyHustle.\n\n"
        "Type /help to see your commands. 🛡️"
    )
