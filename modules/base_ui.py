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

from modules.sheets_helper import client
import logging
import datetime
from datetime import timezone
from telegram.helpers import escape_markdown
from modules.building_system import apply_building_effects

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
        all_players = client.list_all_players()
        user_ids_to_tick = [int(player["user_id"]) for player in all_players if player.get("user_id")]
        logger.info(f"Found {len(user_ids_to_tick)} players for global tick.")
    else:
        logger.warning("tick_resources called without a valid context (neither explicit user_id nor job).")
        return

    for uid in user_ids_to_tick:
        try:
            # Get player data
            player_data = client.get_player_data(uid)
            if not player_data:
                continue

            # Calculate time since last tick
            last_tick = datetime.datetime.fromisoformat(player_data.get('last_tick', '2000-01-01T00:00:00'))
            now = datetime.datetime.now(timezone.utc)
            hours_passed = (now - last_tick).total_seconds() / 3600

            # Calculate production based on building levels
            effects = apply_building_effects(player_data)
            resources = player_data.get('resources', {})
            
            # Add resources based on production rates
            for resource in ['wood', 'stone', 'food', 'gold']:
                production_key = f'{resource}_production_per_hour'
                if production_key in effects:
                    current = resources.get(resource, 0)
                    produced = effects[production_key] * hours_passed
                    capacity = effects.get(f'{resource}_capacity', 1000)
                    resources[resource] = min(current + produced, capacity)

            # Update player data
            player_data['resources'] = resources
            player_data['last_tick'] = now.isoformat()
            client.update_player_data(uid, player_data)
            
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
    elif callback_data == "TRAIN_MENU":
        from modules.training_system import train_menu
        await train_menu(update, context)
        return
    elif callback_data in ["BUILD_MENU", "RESEARCH_MENU", "BASE_ATTACK", "BASE_QUESTS", "BASE_INFO"]:
        # These will be handled by their respective modules
        return

    # TICK resources up to now
    logger.info("base_handler: Calling tick_resources.")
    await tick_resources(context, user.id)
    logger.info("base_handler: tick_resources completed.")

    data: Dict[str, Any] = client.get_player_data(user.id)
    logger.info(f"base_handler: Player data fetched: {data is not None}")
    if not data:
        if message:
            await message.reply_text(
                "❌ You aren't registered yet\. Send /start to begin\.",
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        logger.warning(f"base_handler: No data for user {user.id}. Sent registration message.")
        return

    # Apply building effects to get updated capacities and rates
    calculated_effects = apply_building_effects(data)

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

    # Get capacities
    wood_cap = calculated_effects.get("wood_capacity", data.get("capacity_wood", 10000))
    stone_cap = calculated_effects.get("stone_capacity", data.get("capacity_stone", 10000))
    food_cap = calculated_effects.get("food_capacity", data.get("capacity_food", 10000))
    gold_cap = calculated_effects.get("gold_capacity", data.get("capacity_gold", 5000))
    research_cap = calculated_effects.get("research_capacity", data.get("capacity_research", 1000))

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
    wood_per_hour = calculated_effects.get("wood_production_per_hour", 0)
    stone_per_hour = calculated_effects.get("stone_production_per_hour", 0)
    food_per_hour = calculated_effects.get("food_production_per_hour", 0)
    gold_per_hour = calculated_effects.get("gold_production_per_hour", 0)
    energy_per_hour = calculated_effects.get("energy_production_per_hour", 0)

    # Format resource production block with proper escaping
    resource_block = (
        "📈 *Resource Production*\n\n"
        f"🌲 Wood: {wood}/{wood_cap}  \(`{escape_markdown(f'+{wood_per_hour:.1f}/hr')}`\)\n"
        f"⛰️ Stone: {stone}/{stone_cap}  \(`{escape_markdown(f'+{stone_per_hour:.1f}/hr')}`\)\n"
        f"🍖 Food: {food}/{food_cap}  \(`{escape_markdown(f'+{food_per_hour:.1f}/hr')}`\)\n"
        f"💰 Gold: {gold}/{gold_cap}  \(`{escape_markdown(f'+{gold_per_hour:.1f}/hr')}`\)\n"
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
        f"🏠 *[Commander {escape_markdown(name)}\'s Base]*",
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
        f"🪵 {wood}/{wood_cap}  🪨 {stone}/{stone_cap}  🥖 {food}/{food_cap}  💰 {gold}/{gold_cap}  💎 {diamonds}",
        f"🔋 Energy: {energy_cur}/{energy_max}",
        "",
        "*Ongoing Activities:*",
        *lines_activities,
        "",
        f"*Your Command Options:*"
    ])

    # Insert into your message
    msg += "\n\n*Army Overview:*\n"
    msg += "\n".join(army_lines)

    if bm_lines:
        msg += "\n\n*Black Market Units:*\n"
        msg += "\n".join(bm_lines)

    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("🏗️ Build", callback_data="BUILD_MENU"),
            InlineKeyboardButton("🪖 Train", callback_data="TRAIN_MENU"),
        ],
        [
            InlineKeyboardButton("🧪 Research", callback_data="RESEARCH_MENU"),
            InlineKeyboardButton("🏪 Black Market", callback_data="BM_MENU"),
        ],
        [
            InlineKeyboardButton("⚔️ Attack", callback_data="BASE_ATTACK"),
            InlineKeyboardButton("📜 Quests", callback_data="BASE_QUESTS"),
        ],
        [
            InlineKeyboardButton("ℹ️ Info", callback_data="BASE_INFO"),
            InlineKeyboardButton("🤝 Alliance", callback_data="ALLIANCE_MENU"),
        ],
    ]

    # Send or edit message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        await message.reply_text(
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )


def setup_base_ui(app: Application) -> None:
    """Set up the base UI command and callback handlers."""
    app.add_handler(CommandHandler("base", base_handler))
    app.add_handler(CallbackQueryHandler(base_handler, pattern="^BASE_MENU$")) 