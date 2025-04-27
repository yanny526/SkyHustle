from telegram import Update
from telegram.ext import ContextTypes

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 **Commander Report** 📜\n\n"
        "💰 Gold: 1,000\n"
        "🧱 Stone: 500\n"
        "🪨 Iron: 300\n"
        "⚡ Energy: 100\n\n"
        "🏰 Empire Status: Rising\n"
        "🗺️ Zone: Unclaimed"
    )
