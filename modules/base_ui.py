# modules/base_ui.py
# ───────────────────────────
# Implements the /base command to show a player's resources and base level,
# with inline buttons to "Build New" or "Train Troops".

from typing import Dict, Any, List, Optional

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

from modules.sheets_helper import get_player_data, update_player_data, list_all_players, _accrue_player_resources_in_sheet
import logging
import datetime
from datetime import timezone
from telegram.helpers import escape_markdown

# Set up logging
logger = logging.getLogger(__name__)

# Stub for ongoing activities until we build that system
def _get_ongoing_activities(user_id: int) -> list[str]:
    return []


async def tick_resources(context: ContextTypes.DEFAULT_TYPE, user_id: Optional[int] = None) -> None:
    """Accrue resources for players based on their last collection time and production rates.

    This function can be called for a specific user (e.g., from /base command)
    or as a repeating job for all active players.
    """
    user_ids_to_tick = []

    if user_id:
        # Single user tick (e.g., from /base command with explicit user_id)
        user_ids_to_tick = [user_id]
        logger.info(f"Ticking resources for explicit user {user_id} from command/update.")
    elif context.job:
        # Global tick (from JobQueue)
        logger.info("Performing global resource tick from JobQueue...")
        all_players = list_all_players()
        user_ids_to_tick = [int(player["user_id"]) for player in all_players if player.get("user_id")]
        logger.info(f"Found {len(user_ids_to_tick)} players for global tick.")
    else:
        logger.warning("tick_resources called without a valid context (neither explicit user_id nor job).")
        return

    for uid in user_ids_to_tick:
        try:
            _accrue_player_resources_in_sheet(uid)
            logger.debug(f"Successfully ticked resources for user {uid}.")
        except Exception as e:
            logger.error(f"Failed to tick resources for user {uid}: {e}")


async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Triggered by /base or callback queries. Fetches the calling user's data and displays
    resources, diamonds, base level, and presents "Build New" / "Train Troops" buttons.
    """
    logger.info("Entering base_handler.")

    # Get user from either message or callback query
    if update.callback_query:
        user = update.callback_query.from_user
        message = update.callback_query.message
        callback_data = update.callback_query.data
    else:
        user = update.effective_user
        message = update.message
        callback_data = None

    if not user:
        logger.warning("base_handler: User object is None.")
        return

    if not message:
        logger.warning("base_handler: Message object is None.")
        return

    logger.info(f"base_handler: User ID: {user.id}, Callback Data: {callback_data}")

    # Handle different menu callbacks
    if callback_data == "BM_MENU":
        # Import here to avoid circular imports
        from modules.black_market import black_market_handler
        await black_market_handler(update, context)
        return
    elif callback_data == "ALLIANCE_MENU":
        # Import here to avoid circular imports
        from modules.alliance_system import alliance_handler
        await alliance_handler(update, context)
        return
    elif callback_data in ["BUILD_MENU", "RESEARCH_MENU", "TRAIN_MENU", "BASE_ATTACK", "BASE_QUESTS", "BASE_INFO"]:
        # These will be handled by their respective modules
        return

    # TICK resources up to now
    logger.info("base_handler: Calling tick_resources.")
    await tick_resources(context, user.id)
    logger.info("base_handler: tick_resources completed.")

    data: Dict[str, Any] = get_player_data(user.id)
    logger.info(f"base_handler: Player data fetched: {data is not None}")
    if not data:
        if message:
            await message.reply_text(
                "❌ You aren't registered yet\. Send /start to begin\.",
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        logger.warning(f"base_handler: No data for user {user.id}. Sent registration message.")
        return

    # Safely pull stats with defaults
    name         = data.get("game_name", "Commander")
    x            = data.get("coord_x", 0)
    y            = data.get("coord_y", 0)
    power        = data.get("power", 0)
    prestige     = data.get("prestige_level", 0)
    base_lvl     = int(data.get("base_level", 1))

    wood         = int(data.get("resources_wood", 0))
    stone        = int(data.get("resources_stone", 0))
    food         = int(data.get("resources_food", 0))
    gold         = int(data.get("resources_gold", 0))
    diamonds     = int(data.get("resources_diamonds", 0))
    energy_cur   = int(data.get("resources_energy", base_lvl * 200))
    energy_max   = int(data.get("energy_max", base_lvl * 200))

    # Army counts
    inf = int(data.get("army_infantry", 0))
    tnk = int(data.get("army_tank",      0))
    art = int(data.get("army_artillery",  0))
    dst = int(data.get("army_destroyer",  0))
    bm1 = int(data.get("army_bm_barrage",     0))
    bm2 = int(data.get("army_venom_reaper",   0))
    bm3 = int(data.get("army_titan_crusher",  0))

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
    lumber_lvl       = int(data.get("lumber_house_level", 1))
    mine_lvl         = int(data.get("mine_level", 1))
    warehouse_lvl    = int(data.get("warehouse_level", 1))
    hospital_lvl     = int(data.get("hospital_level", 1))
    research_lvl     = int(data.get("research_lab_level", 1))
    barracks_lvl     = int(data.get("barracks_level", 1))
    powerplant_lvl   = int(data.get("power_plant_level", 1))
    workshop_lvl     = int(data.get("workshop_level", 1))
    jail_lvl         = int(data.get("jail_level", 1))

    # Building levels
    lines_buildings = [
        f"🪓 Lumber House: {lumber_lvl} ⛏️ Mine: {mine_lvl}",
        f"🧺 Warehouse: {warehouse_lvl} 🏥 Hospital: {hospital_lvl}",
        f"🧪 Research Lab: {research_lvl} 🪖 Barracks: {barracks_lvl}",
        f"🔋 Power Plant: {powerplant_lvl} 🔧 Workshop: {workshop_lvl}",
        f"🚔 Jail: {jail_lvl}",
    ]

    # Production rates per hour based on levels (simplified for now)
    wood_per_hour = lumber_lvl * 60.0 
    stone_per_hour = mine_lvl * 50.0 
    food_per_hour = warehouse_lvl * 40.0 
    gold_per_hour = mine_lvl * 30.0 
    energy_per_hour = powerplant_lvl * 20.0 

    # Format resource production block with proper escaping
    resource_block = (
        "📈 *Resource Production*\n\n"
        f"🌲 Wood: {wood}  \(`{escape_markdown(f'+{wood_per_hour:.1f}/hr')}`\)\n"
        f"⛰️ Stone: {stone}  \(`{escape_markdown(f'+{stone_per_hour:.1f}/hr')}`\)\n"
        f"🍖 Food: {food}  \(`{escape_markdown(f'+{food_per_hour:.1f}/hr')}`\)\n"
        f"💰 Gold: {gold}  \(`{escape_markdown(f'+{gold_per_hour:.1f}/hr')}`\)\n"
        f"⚡ Energy: {energy_cur}/{energy_max}  \(`{escape_markdown(f'+{energy_per_hour:.1f}/hr')}`\)\n"
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
            InlineKeyboardButton("🎒 Inventory", callback_data="SHOW_INVENTORY"),
        ],
        [
            InlineKeyboardButton("🤝 Alliances", callback_data="ALLIANCE_MENU"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send or edit message based on context
    if update.callback_query:
        logger.info("base_handler: Attempting to edit message.")
        try:
            await message.edit_text(
                msg,
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup,
            )
            logger.info("base_handler: Message edited successfully.")
        except Exception as e:
            logger.error(f"base_handler: Failed to edit message: {e}")
            # Fallback to sending new message if edit fails
            logger.info("base_handler: Falling back to sending new message.")
            await message.reply_text(
                msg,
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup,
            )
            logger.info("base_handler: Fallback message sent.")
    else:
        logger.info("base_handler: Attempting to send new message.")
        await message.reply_text(
            msg,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup,
        )
        logger.info("base_handler: New message sent successfully.")

def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    # Import handlers here to avoid circular imports
    from modules.black_market import setup_black_market
    from modules.alliance_system import setup_alliance_system

    # Register base command and callback handlers
    app.add_handler(CommandHandler("base", base_handler))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BUILD_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^RESEARCH_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^TRAIN_MENU$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_ATTACK$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_QUESTS$"))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_INFO$"))
    
    # Register black market and alliance handlers
    setup_black_market(app)
    setup_alliance_system(app) 