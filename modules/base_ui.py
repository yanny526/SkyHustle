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
    CallbackQueryHandler,
)

from modules.sheets_helper import get_player_data, tick_resources, update_player_data
from modules.resource_system import tick_resources
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Stub for ongoing activities until we build that system
def _get_ongoing_activities(user_id: int) -> list[str]:
    return []

async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Triggered by /base or callback queries. Fetches the calling user's data and displays
    resources, diamonds, base level, and presents "Build New" / "Train Troops" buttons.
    """
    # Get user from either message or callback query
    if update.callback_query:
        user = update.callback_query.from_user
        message = update.callback_query.message
    else:
        user = update.effective_user
        message = update.message

    if not user:
        return

    # TICK resources up to now
    try:
        await tick_resources(user.id)
    except Exception as e:
        logger.error(f"Resource tick failed: {e}")
        # Continue with base display even if tick fails

    data: Dict[str, Any] = get_player_data(user.id)
    if not data:
        if message:
            await message.reply_text(
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

    # Army counts
    inf = data.get("army_infantry", 0)
    tnk = data.get("army_tank",      0)
    art = data.get("army_artillery",  0)
    dst = data.get("army_destroyer",  0)
    bm1 = data.get("army_bm_barrage",     0)
    bm2 = data.get("army_venom_reaper",   0)
    bm3 = data.get("army_titan_crusher",  0)

    army_lines = [
        f"👣 Infantry: {inf}",
        f"🛡️ Tanks: {tnk}",
        f"🎯 Artillery: {art}",
        f"💥 Destroyers: {dst}",
    ]
    bm_lines = [
        f"🧨 BM Barrage: {bm1}"   if bm1 else None,
        f"🦂 Venom Reapers: {bm2}" if bm2 else None,
        f"🦾 Titan Crushers: {bm3}"if bm3 else None,
    ]
    # Filter out zero lines
    bm_lines = [l for l in bm_lines if l is not None]

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

    # Calculate per-minute production rates
    wood_per_minute = lumber_lvl * 1.0
    stone_per_minute = mine_lvl * 0.8
    food_per_minute = warehouse_lvl * 0.7
    gold_per_minute = mine_lvl * 0.5
    energy_per_minute = powerplant_lvl * 0.3

    # Format resource production block with proper escaping
    resource_block = (
        "📈 *Resource Production*\n\n"
        f"🌲 Wood: {wood}  (`+{wood_per_minute:.1f}/min`)\n"
        f"⛰️ Stone: {stone}  (`+{stone_per_minute:.1f}/min`)\n"
        f"🍖 Food: {food}  (`+{food_per_minute:.1f}/min`)\n"
        f"💰 Gold: {gold}  (`+{gold_per_minute:.1f}/min`)\n"
        f"⚡ Energy: {energy_cur}/{energy_max}  (`+{energy_per_minute:.1f}/min`)\n"
        "――――――――――――"
    )

    # Ongoing activities
    activities = _get_ongoing_activities(user.id)
    if activities:
        lines_activities = [f"- {act}" for act in activities]
    else:
        lines_activities = ["None"]

    # Build the message with proper escaping
    msg = "\n".join([
        f"🏠 *[Commander {name}'s Base]*",
        f"📍 Coordinates: X:{x}, Y:{y}",
        f"📈 Power: {power}",
        f"🧬 Prestige Level: {prestige}",
        f"🏗️ Base Level: {base_lvl}",
        "",
        "*Building Levels:*",
        *lines_buildings,
        "",
        resource_block,
        "",
        "*Current Resources:*",
        f"🪵 {wood}  🪨 {stone}  🥖 {food}  💰 {gold}  💎 {diamonds}",
        f"🔋 Energy: {energy_cur}/{energy_max}",
        "",
        "*Ongoing Activities:*",
        *lines_activities,
        "",
        "*Your Command Options:*",
        "[⚒️ Build] [🧪 Research] [🪖 Train]",
        "[⚔️ Attack] [🎖 Quests] [📊 Building Info]",
    ])

    # Insert into your message
    msg += "\n\n*Army Overview:*\n"
    msg += "\n".join(army_lines)

    if bm_lines:
        msg += "\n\n*Black Market Units:*\n"
        msg += "\n".join(bm_lines)

    keyboard = [
        [
            InlineKeyboardButton("⚒️ Build", callback_data="BUILD_MENU"),
            InlineKeyboardButton("🧪 Research", callback_data="RESEARCH_MENU"),
            InlineKeyboardButton("🪖 Train", callback_data="TRAIN_MENU"),
        ],
        [
            InlineKeyboardButton("⚔️ Attack", callback_data="BASE_ATTACK"),
            InlineKeyboardButton("🎖 Quests", callback_data="BASE_QUESTS"),
            InlineKeyboardButton("📊 Building Info", callback_data="BASE_INFO"),
        ],
        [
            InlineKeyboardButton("🕶️ Black Market", callback_data="BM_MENU"),
        ],
        [
            InlineKeyboardButton("🎒 Inventory", callback_data="INV_BACK"),
        ],
        [
            InlineKeyboardButton("🤝 Alliances", callback_data="ALLIANCE_MENU"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send or edit message based on context
    if update.callback_query:
        try:
            await message.edit_text(
                msg,
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Fallback to sending new message if edit fails
            await message.reply_text(
                msg,
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
    else:
        await message.reply_text(
            msg,
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )

def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    app.add_handler(CommandHandler("base", base_handler))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BUILD_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^RESEARCH_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^TRAIN_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_ATTACK$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_QUESTS$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_INFO$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BM_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^ALLIANCE_MENU$")) 