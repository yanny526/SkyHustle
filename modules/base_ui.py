# modules/base_ui.py
# ───────────────────────────
# Implements the /base command to show a player's resources and base level,
# with inline buttons to "Build New" or "Train Troops".

from typing import Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from modules.sheets_helper import get_player_data

def _get_ongoing_activities(user_id: int) -> list:
    """Stub function for ongoing activities."""
    return []

async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Triggered by /base. Fetches the calling user's data and displays
    resources, diamonds, base level, and presents "Build New" / "Train Troops" buttons.
    """
    user = update.effective_user
    if not user:
        return

    # Fetch player data
    data = get_player_data(user.id)
    if not data:
        await update.message.reply_text("❌ You aren't registered yet. Send /start.")
        return

    # Extract basic info
    name = data["game_name"]
    coord_x = data["coord_x"]
    coord_y = data["coord_y"]
    power = 0  # TODO: Implement power calculation
    prestige = 0  # TODO: Implement prestige system

    # Extract resources
    wood = data["resources_wood"]
    stone = data["resources_stone"]
    gold = data["resources_gold"]
    food = data["resources_food"]
    diamonds = data["diamonds"]

    # Calculate energy
    energy_max = data["base_level"] * 200
    energy = energy_max  # Full energy for now

    # Extract building levels
    lumber_house_level = data["lumber_house_level"]
    mine_level = data["mine_level"]
    warehouse_level = data["warehouse_level"]
    hospital_level = data["hospital_level"]
    research_lab_level = data["research_lab_level"]
    barracks_level = data["barracks_level"]
    power_plant_level = data["power_plant_level"]
    workshop_level = data["workshop_level"]
    jail_level = data["jail_level"]

    # Calculate hourly outputs
    wood_output = lumber_house_level * 60
    stone_output = mine_level * 45
    food_output = warehouse_level * 50
    gold_output = mine_level * 30
    energy_output = power_plant_level * 20

    # Build the message
    message = (
        f"🏠 [Commander {name}'s Base]\n"
        f"📍 Coordinates: X:{coord_x}, Y:{coord_y}\n"
        f"📈 Power: {power}\n"
        f"🧬 Prestige Level: {prestige}\n"
        f"🏗️ Base Level: {data['base_level']}\n\n"
        f"🧱 Building Levels:\n\n"
        f"🪓 Lumber House: {lumber_house_level} ⛏️ Mine: {mine_level}\n\n"
        f"🧺 Warehouse: {warehouse_level} 🏥 Hospital: {hospital_level}\n\n"
        f"🧪 Research Lab: {research_lab_level} 🪖 Barracks: {barracks_level}\n\n"
        f"🔋 Power Plant: {power_plant_level} 🔧 Workshop: {workshop_level}\n\n"
        f"🚔 Jail: {jail_level}\n\n"
        f"📤 Hourly Output:\n\n"
        f"🪵 Wood: +{wood_output}/hr 🪨 Stone: +{stone_output}/hr\n\n"
        f"🥖 Food: +{food_output}/hr 💰 Gold: +{gold_output}/hr\n\n"
        f"🔋 Energy: +{energy_output}/hr\n\n"
        f"💰 Current Resources:\n"
        f"🪵 {wood} 🪨 {stone} 🥖 {food} 💰 {gold} 💎 {diamonds}\n"
        f"🔋 Energy: {energy}/{energy_max}\n\n"
        f"🛠️ Ongoing Activities:\n\n"
    )

    # Add ongoing activities
    activities = _get_ongoing_activities(user.id)
    if not activities:
        message += "None\n\n"
    else:
        for activity in activities:
            message += f"• {activity}\n"
        message += "\n"

    # Add command options
    message += "🎯 Your Command Options:"

    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("⚒️ Build", callback_data="build"),
            InlineKeyboardButton("🧪 Research", callback_data="research"),
            InlineKeyboardButton("🪖 Train", callback_data="train"),
        ],
        [
            InlineKeyboardButton("⚔️ Attack", callback_data="attack"),
            InlineKeyboardButton("🎖 Quests", callback_data="quests"),
            InlineKeyboardButton("🛒 Shop", callback_data="shop"),
        ],
        [InlineKeyboardButton("🏠 Back to Base", callback_data="base")],
    ]

    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN,
    )

def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    app.add_handler(CommandHandler("base", base_handler)) 