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
            missions_text += f"\u2022 *{mission_name}*\n   ➔ 🎯 Objective: {objective}\n   ➔ 💰 Reward: {reward} Gold\n\n"
        except Exception as e:
            print(f"Error parsing mission: {e}")

    missions_text += "✨ Complete missions to earn rewards and glory!"

    await update.message.reply_text(missions_text, parse_mode="Markdown")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow player to claim a mission reward."""
    telegram_id = update.effective_user.id
    row = db.find_player(telegram_id)

    if not row:
        return await update.message.reply_text("⚠️ You don't have a SkyHustle profile yet! Use /start first!")

    if len(context.args) < 1:
        return await update.message.reply_text("🎯 Usage: /claimmission <mission_name>")

    mission_name = " ".join(context.args).strip()

    mission_sheet = db.missions
    progress_sheet = db.mission_progress

    missions_data = mission_sheet.get_all_values()
    progress_data = progress_sheet.get_all_values()

    # Check if mission exists
    found_mission = None
    for mission in missions_data[1:]:  # Skip header
        if mission[0].lower() == mission_name.lower():
            found_mission = mission
            break

    if not found_mission:
        return await update.message.reply_text("❌ Mission not found! Check spelling carefully.")

    # Check if player already claimed
    for record in progress_data[1:]:
        if record[0] == str(telegram_id) and record[1].lower() == mission_name.lower():
            return await update.message.reply_text("⚠️ You've already claimed this mission reward!")

    # If passed, give reward
    reward_gold = int(found_mission[2])
    db.update_player_resources(telegram_id, gold_delta=reward_gold)

    # Save progress
    progress_sheet.append_row([str(telegram_id), found_mission[0]])

    await update.message.reply_text(
        f"🎉 Mission **{found_mission[0]}** completed!\n"
        f"💰 You earned **{reward_gold} Gold**!\n"
        f"🏆 Congratulations, Commander!",
        parse_mode="Markdown"
    )
