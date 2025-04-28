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

    missions_text = "🎯 *Available Missions* 🎯\n\n"

    for mission in missions_data[1:]:  # Skip header
        try:
            mission_name = mission[0]
            objective = mission[1]
            reward = mission[2]
            missions_text += (
                f"• *{mission_name}*\n"
                f"   ➔ 🎯 Objective: {objective}\n"
                f"   ➔ 💰 Reward: {reward} Gold\n\n"
            )
        except Exception as e:
            print(f"Error parsing mission: {e}")

    missions_text += "✨ Complete missions to earn rewards and glory!"

    await update.message.reply_text(missions_text, parse_mode="Markdown")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow player to claim a mission reward."""
    telegram_id = update.effective_user.id

    player = db.get_player_data(telegram_id)
    if not player:
        return await update.message.reply_text("⚠️ You don't have a SkyHustle profile yet! Use /start first!")

    # Check if missions exist
    mission_sheet = db.missions
    missions_data = mission_sheet.get_all_values()

    if not missions_data or len(missions_data) <= 1:
        return await update.message.reply_text("🚫 No missions available to claim!")

    # For now: always grant 500 Gold (temporary logic)
    reward_amount = 500
    db.update_player_resources(telegram_id, gold_delta=reward_amount)

    await update.message.reply_text(
        "🎉 *Mission completed!* 🎉\n"
        "💰 You earned *+500 Gold*!\n"
        "🏆 Keep completing more missions to dominate SkyHustle!",
        parse_mode="Markdown"
    )
