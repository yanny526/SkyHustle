# handlers/missions.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available missions."""
    telegram_id = update.effective_user.id
    row = db.find_player(telegram_id)

    if not row:
        return await update.message.reply_text("⚠️ You don't have a SkyHustle profile yet! Use /start first!")

    mission_sheet = db.missions
    missions_data = mission_sheet.get_all_values()

    if not missions_data or len(missions_data) <= 1:
        return await update.message.reply_text("🎯 No missions available at the moment!")

    missions_text = "🎯 **Available Missions** 🎯\n\n"

    for mission in missions_data[1:]:  # Skip header
        try:
            if len(mission) >= 3:
                mission_name = mission[0]
                objective = mission[1]
                reward = mission[2]
                missions_text += (
                    f"• 🛡️ *{mission_name}*\n"
                    f"   ➔ 🎯 Objective: {objective}\n"
                    f"   ➔ 💰 Reward: {reward} Gold\n\n"
                )
        except Exception as e:
            print(f"Error parsing mission: {e}")

    missions_text += "✨ Complete missions daily to build your empire faster! ✨"

    await update.message.reply_text(missions_text, parse_mode="Markdown")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for claiming missions (coming soon)."""
    await update.message.reply_text("🎁 Mission claiming feature coming soon!")
