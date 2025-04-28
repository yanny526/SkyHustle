# handlers/missions.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available missions that player hasn't completed yet."""
    telegram_id = update.effective_user.id
    row = db.find_player(telegram_id)

    if not row:
        return await update.message.reply_text("⚠️ You don't have a SkyHustle profile yet! Use /start first!")

    mission_sheet = db.missions
    progress_sheet = db.mission_progress

    missions_data = mission_sheet.get_all_values()
    progress_data = progress_sheet.get_all_values()

    if not missions_data or len(missions_data) <= 1:
        return await update.message.reply_text("🎯 No missions available at the moment!")

    # Find player's completed missions
    completed_missions = []
    if progress_data and len(progress_data) > 1:
        for record in progress_data[1:]:  # Skip header
            if record[0] == str(telegram_id):
                completed_missions.append(record[1])

    missions_text = "🎯 *Available Missions* 🎯\n\n"
    available_count = 0

    for mission in missions_data[1:]:  # Skip header
        mission_name = mission[0]
        objective = mission[1]
        reward = mission[2]

        if mission_name not in completed_missions:
            missions_text += f"• *{mission_name}*\n   ➔ 🎯 Objective: {objective}\n   ➔ 💰 Reward: {reward} Gold\n\n"
            available_count += 1

    if available_count == 0:
        return await update.message.reply_text("🎯 No missions available at the moment!")

    missions_text += "✨ Complete missions to earn rewards and glory!"
    await update.message.reply_text(missions_text, parse_mode="Markdown")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow player to claim a mission reward (placeholder)."""
    await update.message.reply_text("🎁 Mission claiming feature coming soon!")
