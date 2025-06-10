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

    # Safely pull stats with defaults
    name         = data.get("game_name", "Commander")
    x            = data.get("coord_x", 0)
    y            = data.get("coord_y", 0)
    power        = data.get("power", 0)
    prestige     = data.get("prestige_level", 0)
    base_lvl     = data.get("base_level", 1)

    wood         = data.get("resources_wood", 0)
    stone        = data.get("resources_stone", 0)
    food         = data.get("resources_food", 0)
    gold         = data.get("resources_gold", 0)
    diamonds     = data.get("diamonds", 0)
    energy_cur   = data.get("energy", base_lvl * 200)
    energy_max   = data.get("energy_max", base_lvl * 200)

    # Building levels (default to 1)
    lumber_lvl       = data.get("lumber_house_level", 1)
    mine_lvl         = data.get("mine_level", 1)
    warehouse_lvl    = data.get("warehouse_level", 1)
    hospital_lvl     = data.get("hospital_level", 1)
    research_lvl     = data.get("research_lab_level", 1)
    barracks_lvl     = data.get("barracks_level", 1)
    powerplant_lvl   = data.get("power_plant_level", 1)
    workshop_lvl     = data.get("workshop_level", 1)
    jail_lvl         = data.get("jail_level", 1)

    # Building levels
    lines_buildings = [
        f"🪓 Lumber House: {lumber_lvl} ⛏️ Mine: {mine_lvl}",
        f"🧺 Warehouse: {warehouse_lvl} 🏥 Hospital: {hospital_lvl}",
        f"🧪 Research Lab: {research_lvl} 🪖 Barracks: {barracks_lvl}",
        f"🔋 Power Plant: {powerplant_lvl} 🔧 Workshop: {workshop_lvl}",
        f"🚔 Jail: {jail_lvl}",
    ]

    # Hourly outputs
    wood_out = lumber_lvl * 60
    stone_out = mine_lvl * 45
    food_out = warehouse_lvl * 50
    gold_out = mine_lvl * 30
    energy_out = powerplant_lvl * 20
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
            InlineKeyboardButton("⚒️ Build", callback_data="BUILD_MENU"),
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