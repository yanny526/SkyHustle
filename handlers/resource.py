from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    updated = db.update_player_resources(user.id, gold_delta=500, stone_delta=250, iron_delta=150, energy_delta=50)
    
    if updated:
        await update.message.reply_text(
            "🎁 **Daily Bonus Claimed!** 🎁\n\n"
            "💰 +500 Gold\n"
            "🧱 +250 Stone\n"
            "🪨 +150 Iron\n"
            "⚡ +50 Energy\n\n"
            "Return tomorrow for greater rewards! ✨"
        )
    else:
        await update.message.reply_text("⚠️ You need to create your empire first! Type /start.")

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    updated = db.update_player_resources(user.id, gold_delta=100, stone_delta=50, iron_delta=30)
    
    if updated:
        await update.message.reply_text(
            "⛏️ **Mining Expedition Successful!** ⛏️\n\n"
            "💰 +100 Gold | 🧱 +50 Stone | 🪨 +30 Iron\n"
            "⛏️ Your miners return triumphantly!"
        )
    else:
        await update.message.reply_text("⚠️ You need to create your empire first! Type /start.")

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    updated = db.update_player_resources(user.id, gold_delta=200, stone_delta=100, iron_delta=75)
    
    if updated:
        await update.message.reply_text(
            "📦 **Resources Collected!** 📦\n\n"
            "💰 +200 Gold | 🧱 +100 Stone | 🪨 +75 Iron\n"
            "Your storage vaults grow heavier with treasure!"
        )
    else:
        await update.message.reply_text("⚠️ You need to create your empire first! Type /start.")
