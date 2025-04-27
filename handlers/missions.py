from telegram import Update
from telegram.ext import ContextTypes
import json
import utils.db as db

# Load missions from JSON
def load_missions():
    with open("data/missions.json", "r") as f:
        data = json.load(f)
    return data["missions"]

async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all available missions."""
    all_missions = load_missions()

    mission_text = "🎯 **Today's Missions** 🎯\n\n"
    for mission in all_missions:
        mission_text += (
            f"🆔 {mission['id']}\n"
            f"📜 {mission['description']}\n"
            f"🏆 Rewards: {mission['reward_gold']} Gold, {mission['reward_stone']} Stone, {mission['reward_iron']} Iron\n\n"
        )

    await update.message.reply_text(mission_text)

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim a mission reward by mission ID."""
    telegram_id = update.effective_user.id

    if len(context.args) != 1:
        return await update.message.reply_text("🎯 Usage: /claim <mission_id>")

    mission_id = context.args[0].upper()
    all_missions = load_missions()

    # Find the mission
    selected_mission = None
    for mission in all_missions:
        if mission["id"].upper() == mission_id:
            selected_mission = mission
            break

    if not selected_mission:
        return await update.message.reply_text("🎯 Mission ID not found!")

    # 🔥 For now: assume player always completed the mission
    db.update_player_resources(
        telegram_id,
        gold_delta=selected_mission["reward_gold"],
        stone_delta=selected_mission["reward_stone"],
        iron_delta=selected_mission["reward_iron"]
    )

    await update.message.reply_text(
        f"🎯 Mission {mission_id} completed!\n"
        f"🏆 Rewards collected: +{selected_mission['reward_gold']} Gold, "
        f"+{selected_mission['reward_stone']} Stone, +{selected_mission['reward_iron']} Iron!"
    )
