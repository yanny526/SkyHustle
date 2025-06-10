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

# Stub for ongoing activities until we build that system
def _get_ongoing_activities(user_id: int) -> list[str]:
    return []

async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Triggered by /base. Fetches the calling user's data and displays
    resources, diamonds, base level, and presents "Build New" / "Train Troops" buttons.
    """
    user = update.effective_user
    uid = user.id

    data: Dict[str, Any] = get_player_data(uid)
    if not data:
        await update.message.reply_text(
            "❌ You aren't registered yet. Send /start to begin.",
        )
        return

    # Core stats
    name = data["game_name"]
    x, y = data["coord_x"], data["coord_y"]
    power = data["power"]
    prestige = data["prestige_level"]
    base_lvl = data["base_level"]

    # Resources
    wood = data["resources_wood"]
    stone = data["resources_stone"]
    food = data["resources_food"]
    gold = data["resources_gold"]
    diamonds = data["diamonds"]
    energy_cur = data.get("energy", base_lvl * 200)
    energy_max = data.get("energy_max", base_lvl * 200)

    # Building levels
    b = data  # shorthand
    lines_buildings = [
        f"🪓 Lumber House: {b['lumber_house_level']} ⛏️ Mine: {b['mine_level']}",
        f"🧺 Warehouse: {b['warehouse_level']} 🏥 Hospital: {b['hospital_level']}",
        f"🧪 Research Lab: {b['research_lab_level']} 🪖 Barracks: {b['barracks_level']}",
        f"🔋 Power Plant: {b['power_plant_level']} 🔧 Workshop: {b['workshop_level']}",
        f"🚔 Jail: {b['jail_level']}",
    ]

    # Hourly outputs
    wood_out = b["lumber_house_level"] * 60
    stone_out = b["mine_level"] * 45
    food_out = b["warehouse_level"] * 50
    gold_out = b["mine_level"] * 30
    energy_out = b["power_plant_level"] * 20
    lines_output = [
        f"- 🪵 Wood: +{wood_out}/hr 🪨 Stone: +{stone_out}/hr",
        f"- 🥖 Food: +{food_out}/hr 💰 Gold: +{gold_out}/hr",
        f"- 🔋 Energy: +{energy_out}/hr",
    ]

    # Ongoing activities
    activities = _get_ongoing_activities(uid)
    if activities:
        lines_activities = [f"- {act}" for act in activities]
    else:
        lines_activities = ["None"]

    # Build the message
    msg = "\n".join([
        f"🏠 *[Commander {name}'s Base]*",
        f"📍 Coordinates: X:{x}, Y:{y}",
        f"📈 Power: {power}",
        f"🧬 Prestige Level: {prestige}",
        f"🏗️ Base Level: {base_lvl}",
        "",
        "🧱 *Building Levels:*",
        *lines_buildings,
        "",
        "📤 *Hourly Output:*",
        *lines_output,
        "",
        "💰 *Current Resources:*",
        f"🪵 {wood} 🪨 {stone} 🥖 {food} 💰 {gold} 💎 {diamonds}",
        f"🔋 Energy: {energy_cur}/{energy_max}",
        "",
        "🛠️ *Ongoing Activities:*",
        *lines_activities,
        "",
        "🎯 *Your Command Options:*",
        "[⚒️ Build] [🧪 Research] [🪖 Train]",
        "[⚔️ Attack] [🎖 Quests] [📊 Building Info]",
    ])

    keyboard = [
        [
            InlineKeyboardButton("⚒️ Build", callback_data="BASE_BUILD"),
            InlineKeyboardButton("🧪 Research", callback_data="BASE_RESEARCH"),
            InlineKeyboardButton("🪖 Train", callback_data="BASE_TRAIN"),
        ],
        [
            InlineKeyboardButton("⚔️ Attack", callback_data="BASE_ATTACK"),
            InlineKeyboardButton("🎖 Quests", callback_data="BASE_QUESTS"),
            InlineKeyboardButton("📊 Building Info", callback_data="BASE_INFO"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        msg,
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )

def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    app.add_handler(CommandHandler("base", base_handler)) 