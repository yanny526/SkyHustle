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

from modules.sheets_helper import (
    get_player_data, update_player_data, list_all_players, 
    _accrue_player_resources_in_sheet, get_pending_upgrades, get_due_upgrades
)
from modules.building_system import BUILDING_CONFIG, _BUILDING_KEY_TO_FIELD, get_building_info
from modules.research_system import get_active_research, RESEARCH_CATALOG, complete_research
import logging
import datetime
from datetime import timezone
from telegram.helpers import escape_markdown
import math
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

def _get_ongoing_activities(user_id: int) -> list[str]:
    activities = []
    
    # Check for building upgrades
    upgrades = get_pending_upgrades()
    user_upgrades = [u for u in upgrades if u["user_id"] == user_id]
    for upgrade in user_upgrades:
        building_name = escape_markdown(BUILDING_CONFIG[upgrade["building_key"]]["name"], version=2)
        end_time = upgrade["finish_at"].strftime("%H:%M UTC")
        activities.append(f"🔨 {building_name} to level {upgrade['new_level']} \\(Completes at {end_time}\\)")
    
    # Check for research projects
    active_research = get_active_research(user_id)
    if active_research:
        remaining_time = active_research.end_timestamp - datetime.datetime.now(timezone.utc)
        if remaining_time.total_seconds() > 0:
            hours, remainder = divmod(remaining_time.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            remaining_str = f"{int(hours):02d}:{int(minutes):02d}:{(remaining_time.total_seconds() % 60):02.0f}"
            activities.append(f"🧪 {escape_markdown(active_research.name, version=2)} \\(Completes in {escape_markdown(remaining_str, version=2)}\\)")

    # Check for troop training
    data = get_player_data(user_id)
    if data and data.get("training_timer"):
        try:
            training_end = datetime.datetime.fromisoformat(data["training_timer"].replace("Z", "+00:00"))
            if training_end > datetime.datetime.now(timezone.utc):
                unit_name = escape_markdown(data.get("training_unit", "Unknown Unit"), version=2)
                quantity = data.get("training_quantity", 0)
                end_time = training_end.strftime("%H:%M UTC")
                activities.append(f"🪖 Training {quantity} {unit_name} \\(Completes at {end_time}\\)")
        except (ValueError, TypeError):
            pass
    
    return activities


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
    """Handle the /base command and base menu interactions."""
    logger.info("Entering base_handler.")
    
    if not update.effective_user:
        return
    
    user = update.effective_user
    logger.info(f"base_handler: User ID: {user.id}, Callback Data: {update.callback_query.data if update.callback_query else None}")
    
    # Always tick resources first
    logger.info("base_handler: Calling tick_resources.")
    await tick_resources(context, user.id)
    logger.info("base_handler: tick_resources completed.")
    
    # Get player data
    player_data = get_player_data(user.id)
    logger.info(f"base_handler: Player data fetched: {bool(player_data)}")
    
    if not player_data:
        await update.message.reply_text(
            "You haven't registered yet! Use /start to begin.",
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return
    
    # Safely pull stats with defaults
    name         = player_data.get("game_name", "Commander")
    x            = player_data.get("coord_x", 0)
    y            = player_data.get("coord_y", 0)
    power        = player_data.get("power", 0)
    prestige     = player_data.get("prestige_level", 0)
    base_lvl     = int(player_data.get("base_level", 1))

    wood         = int(player_data.get("resources_wood", 0))
    stone        = int(player_data.get("resources_stone", 0))
    food         = int(player_data.get("resources_food", 0))
    gold         = int(player_data.get("resources_gold", 0))
    diamonds     = int(player_data.get("resources_diamonds", 0))
    energy_cur   = int(player_data.get("resources_energy", base_lvl * 200))
    energy_max   = int(player_data.get("energy_max", base_lvl * 200))

    # Army counts
    inf = int(player_data.get("army_infantry", 0))
    tnk = int(player_data.get("army_tank",      0))
    art = int(player_data.get("army_artillery",  0))
    dst = int(player_data.get("army_destroyer",  0))
    bm1 = int(player_data.get("army_bm_barrage",     0))
    bm2 = int(player_data.get("army_venom_reaper",   0))
    bm3 = int(player_data.get("army_titan_crusher",  0))

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
    lumber_lvl       = int(player_data.get("lumber_house_level", 1))
    mine_lvl         = int(player_data.get("mine_level", 1))
    warehouse_lvl    = int(player_data.get("warehouse_level", 1))
    hospital_lvl     = int(player_data.get("hospital_level", 1))
    research_lvl     = int(player_data.get("research_lab_level", 1))
    barracks_lvl     = int(player_data.get("barracks_level", 1))
    powerplant_lvl   = int(player_data.get("power_plant_level", 1))
    workshop_lvl     = int(player_data.get("workshop_level", 1))
    jail_lvl         = int(player_data.get("jail_level", 1))

    # Building levels display
    lines_buildings = [
        f"🪓 {escape_markdown('Lumber House', version=2)}: {lumber_lvl} ⛏️ {escape_markdown('Mine', version=2)}: {mine_lvl}",
        f"🧺 {escape_markdown('Warehouse', version=2)}: {warehouse_lvl} 🏥 {escape_markdown('Hospital', version=2)}: {hospital_lvl}",
        f"🧪 {escape_markdown('Research Lab', version=2)}: {research_lvl} 🪖 {escape_markdown('Barracks', version=2)}: {barracks_lvl}",
        f"🔋 {escape_markdown('Power Plant', version=2)}: {powerplant_lvl} 🔧 {escape_markdown('Workshop', version=2)}: {workshop_lvl}",
        f"🚔 {escape_markdown('Jail', version=2)}: {jail_lvl}",
    ]

    # Production rates per hour based on levels (simplified for now)
    wood_per_hour = lumber_lvl * 60.0 
    stone_per_hour = mine_lvl * 50.0 
    food_per_hour = warehouse_lvl * 40.0 
    gold_per_hour = mine_lvl * 30.0 
    energy_per_hour = powerplant_lvl * 20.0 

    # Format resource production block with proper escaping
    resource_block = (
        f"📈 *{escape_markdown('Resource Production', version=2)}*\n\n"
        f"🌲 Wood: {wood}  \\(\\`{escape_markdown(f'+{wood_per_hour:.1f}/hr', version=2)}\\`\\)\n"
        f"⛰️ Stone: {stone}  \\(\\`{escape_markdown(f'+{stone_per_hour:.1f}/hr', version=2)}\\`\\)\n"
        f"🍖 Food: {food}  \\(\\`{escape_markdown(f'+{food_per_hour:.1f}/hr', version=2)}\\`\\)\n"
        f"💰 Gold: {gold}  \\(\\`{escape_markdown(f'+{gold_per_hour:.1f}/hr', version=2)}\\`\\)\n"
        f"⚡ Energy: {energy_cur}/{energy_max}  \\(\\`{escape_markdown(f'+{energy_per_hour:.1f}/hr', version=2)}\\`\\)\n"
        f"\-\-\-\-\-\-\-\-\-\-\-\-\-"
    )

    # Get ongoing activities
    activities = _get_ongoing_activities(user.id)
    lines_activities = [escape_markdown(act, version=2) for act in activities]
    if not lines_activities:
        lines_activities = [escape_markdown("None", version=2)]

    # Build the message with proper escaping
    msg = "\n".join([
        f"🏠 *[Commander {escape_markdown(name, version=2)}\'s Base]*",
        f"📍 Coordinates: X:{escape_markdown(str(x), version=2)}, Y:{escape_markdown(str(y), version=2)}",
        f"📈 Power: {power}",
        f"🧬 Prestige Level: {prestige}",
        f"🏗️ Base Level: {base_lvl}",
        "",
        f"*{escape_markdown('Building Levels:', version=2)}*",
        *lines_buildings,
        "",
        resource_block,
        "",
        f"*{escape_markdown('Current Resources:', version=2)}*",
        f"🪵 {wood}  🪨 {stone}  🥖 {food}  💰 {gold}  💎 {diamonds}",
        f"🔋 Energy: {energy_cur}/{energy_max}",
        "",
        f"*{escape_markdown('Ongoing Activities:', version=2)}*",
        *lines_activities,
        "",
        f"*{escape_markdown('Your Command Options:', version=2)}*"
    ])

    # Append army overview
    msg += f"\n\n*{escape_markdown('Army Overview:', version=2)}*\n"
    msg += "\n".join([
        f"👣 {escape_markdown('Infantry', version=2)}: {inf}",
        f"🛡️ {escape_markdown('Tanks', version=2)}: {tnk}",
        f"🎯 {escape_markdown('Artillery', version=2)}: {art}",
        f"💥 {escape_markdown('Destroyers', version=2)}: {dst}",
    ])

    # Append black market units if any
    if bm_lines:
        msg += f"\n\n*{escape_markdown('Black Market Units:', version=2)}*\n"
        msg += "\n".join([
            f"🧨 {escape_markdown('BM Barrage', version=2)}: {bm1}"   if bm1 is not None else None,
            f"🦂 {escape_markdown('Venom Reapers', version=2)}: {bm2}" if bm2 is not None else None,
            f"🦾 {escape_markdown('Titan Crushers', version=2)}: {bm3}"if bm3 is not None else None,
        ])
        bm_lines = [l for l in bm_lines if l is not None] # Re-filter after escaping

    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("⚒️ Build", callback_data="BUILD_MENU"),
            InlineKeyboardButton("🧪 Research", callback_data="RESEARCH_MENU"),
            InlineKeyboardButton("🪖 Train", callback_data="TRAIN_MENU"),
        ],
        [
            InlineKeyboardButton("⚔️ Attack", callback_data="BASE_ATTACK"),
            InlineKeyboardButton("🎖 Quests", callback_data="BASE_QUESTS"),
            InlineKeyboardButton("📊 Building Info", callback_data="BUILD_MENU"),
        ],
        [
            InlineKeyboardButton("💰 Black Market", callback_data="BM_MENU"),
            InlineKeyboardButton("🤝 Alliance", callback_data="ALLIANCE_MENU"),
            InlineKeyboardButton("🗺 Zones", callback_data="ZONE_MENU"),
        ],
        [InlineKeyboardButton("🏠 Back to Base", callback_data="base")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or update message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )

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
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BACK_TO_BASE$"))
    
    # Register black market and alliance handlers
    setup_black_market(app)
    setup_alliance_system(app) 