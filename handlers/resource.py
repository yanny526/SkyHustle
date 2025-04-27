from telegram import Update
from telegram.ext import ContextTypes

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 **Daily Bonus Claimed!** 🎁\n\n"
        "💰 +500 Gold\n"
        "🧱 +250 Stone\n"
        "🪨 +150 Iron\n"
        "⚡ +50 Energy\n\n"
        "Return tomorrow for greater riches! ✨"
    )

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⛏️ **Mining Expedition Launched!** ⛏️\n\n"
        "Your miners dig deep beneath the shattered earth...\n"
        "⏳ Resources will be ready to collect soon!"
    )

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 **Resource Collection Complete!** 📦\n\n"
        "💰 +120 Gold | 🧱 +45 Stone | 🪨 +30 Iron\n"
        "⛏️ Your storerooms grow heavier with treasure!"
    )
