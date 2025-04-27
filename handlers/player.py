from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = db.get_player_data(user.id)
    
    if data:
        await update.message.reply_text(
            f"📜 **Commander Report** 📜\n\n"
            f"💰 Gold: {data['Gold']}\n"
            f"🧱 Stone: {data['Stone']}\n"
            f"🪨 Iron: {data['Iron']}\n"
            f"⚡ Energy: {data['Energy']}\n\n"
            f"🏰 Empire Status: {data['Zone']}"
        )
    else:
        await update.message.reply_text("⚠️ You have no empire yet. Type /start to create one!")
