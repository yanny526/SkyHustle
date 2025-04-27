from telegram import Update
from telegram.ext import ContextTypes

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 **Scanning Nearby Territories...** 🔎\n\n"
        "No rival Commanders detected nearby.\n"
        "🛡️ The wastelands are quiet... for now."
    )
