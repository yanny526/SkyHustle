from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan nearby zones (simple version for now)."""
    await update.message.reply_text(
        "🔎 **Scanning Nearby Territories...** 🔎\n\n"
        "No rival Commanders detected nearby.\n"
        "🛡️ The wastelands are quiet... for now."
    )

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim a new Zone."""
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("🏰 Usage: /claim <zonename>")

    zone_name = context.args[0].capitalize()

    if db.is_zone_claimed(zone_name):
        return await update.message.reply_text("🏰 This zone is already claimed by another Commander!")

    db.claim_zone(telegram_id, zone_name)
    await update.message.reply_text(f"🏰 You have claimed Zone {zone_name}! Expand your empire wisely!")

async def zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View your current zone."""
    telegram_id = update.effective_user.id
    zone_name = db.get_zone(telegram_id)

    if not zone_name or zone_name == "Unclaimed":
        return await update.message.reply_text("🏰 You have not claimed any zone yet. Use /claim to conquer territory!")

    await update.message.reply_text(f"🏰 You are currently ruling Zone: {zone_name}")

async def map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View the world map (simple version for now)."""
    await update.message.reply_text(
        "🗺️ **World Map** 🗺️\n\n"
        "- Zone A: Unclaimed\n"
        "- Zone B: Unclaimed\n"
        "- Zone C: Unclaimed\n"
        "- Zone D: Unclaimed\n"
        "- Zone E: Unclaimed\n\n"
        "🏰 Conquer zones with /claim <zonename>!"
    )
