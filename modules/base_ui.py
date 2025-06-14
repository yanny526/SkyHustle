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
    _accrue_player_resources_in_sheet, get_pending_upgrades
)
from modules.building_system import BUILDING_CONFIG, _BUILDING_KEY_TO_FIELD
import logging
import datetime
from datetime import timezone
from telegram.helpers import escape_markdown

# Set up logging
logger = logging.getLogger(__name__)

def _get_ongoing_activities(user_id: int) -> list[str]:
    activities = []
    
    # Check for building upgrades
    upgrades = get_pending_upgrades()
    user_upgrades = [u for u in upgrades if u["user_id"] == user_id]
    for upgrade in user_upgrades:
        building_name = BUILDING_CONFIG[upgrade["building_key"]]["name"]
        end_time = upgrade["finish_at"].strftime("%H:%M UTC")
        activities.append(f"🔨 {building_name} to level {upgrade['new_level']} \\(Completes at {end_time}\\)")
    
    # Check for research projects
    data = get_player_data(user_id)
    if data and data.get("research_timer"):
        try:
            research_end = datetime.datetime.fromisoformat(data["research_timer"].replace("Z", "+00:00"))
            if research_end > datetime.datetime.now(timezone.utc):
                research_name = data.get("research_name", "Unknown Research")
                end_time = research_end.strftime("%H:%M UTC")
                activities.append(f"🧪 {research_name} \\(Completes at {end_time}\\)")
        except (ValueError, TypeError):
            pass
    
    # Check for troop training
    if data and data.get("training_timer"):
        try:
            training_end = datetime.datetime.fromisoformat(data["training_timer"].replace("Z", "+00:00"))
            if training_end > datetime.datetime.now(timezone.utc):
                unit_name = data.get("training_unit", "Unknown Unit")
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
    
    # Get ongoing activities
    activities = _get_ongoing_activities(user.id)
    
    # Format the message
    message = (
        f"*{escape_markdown(player_data['game_name'], version=2)}'s Base*\n\n"
        f"*Resources:*\n"
        f"💰 Gold: {player_data['resources_gold']}/{player_data['capacity_gold']} \\(\\+{player_data['gold_rate']}/min\\)\n"
        f"🪵 Wood: {player_data['resources_wood']}/{player_data['capacity_wood']} \\(\\+{player_data['wood_rate']}/min\\)\n"
        f"📚 Research: {player_data['research_balance']}/{player_data['capacity_research']} \\(\\+{player_data['research_rate']}/min\\)\n"
        f"⚡ Energy: {player_data['resources_energy']}/{player_data['energy_max']}\n\n"
        f"*Buildings:*\n"
        f"🏰 Base: Level {player_data['base_level']}\n"
        f"⛏️ Mine: Level {player_data['mine_level']}\n"
        f"🪓 Lumber House: Level {player_data['lumber_house_level']}\n"
        f"🏪 Warehouse: Level {player_data['warehouse_level']}\n"
        f"⚔️ Barracks: Level {player_data['barracks_level']}\n"
        f"⚡ Power Plant: Level {player_data['power_plant_level']}\n"
        f"🏥 Hospital: Level {player_data['hospital_level']}\n"
        f"🔬 Research Lab: Level {player_data['research_lab_level']}\n"
        f"🔧 Workshop: Level {player_data['workshop_level']}\n"
        f"🔒 Jail: Level {player_data['jail_level']}\n\n"
        f"*Ongoing Activities:*\n"
    )
    
    if activities:
        message += "\n".join(activities)
    else:
        message += "None"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("Upgrade", callback_data="upgrade"),
            InlineKeyboardButton("Research", callback_data="research"),
        ],
        [
            InlineKeyboardButton("Train Troops", callback_data="train"),
            InlineKeyboardButton("Attack", callback_data="attack"),
        ],
        [
            InlineKeyboardButton("Items", callback_data="items"),
            InlineKeyboardButton("Alliance", callback_data="alliance"),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or update message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            message,
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