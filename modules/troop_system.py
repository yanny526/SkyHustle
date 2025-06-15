from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import logging

from modules.sheets_helper import get_player_data, update_player_data
from modules.building_config import BUILDING_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

async def troop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the troop management menu."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    player_data = get_player_data(query.from_user.id)
    if not player_data:
        await query.edit_message_text(
            "❌ You need to register first! Use /start to begin.",
            parse_mode=None
        )
        return
    
    # Get troop counts
    infantry = player_data.get("army_infantry", 0)
    tanks = player_data.get("army_tank", 0)
    artillery = player_data.get("army_artillery", 0)
    destroyers = player_data.get("army_destroyer", 0)
    
    # Format the menu text
    text = (
        "🪖 <b>Troop Management</b>\n\n"
        f"👣 Infantry: {infantry}\n"
        f"🛡️ Tanks: {tanks}\n"
        f"🎯 Artillery: {artillery}\n"
        f"💥 Destroyers: {destroyers}\n\n"
        "Select an option below:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("👣 Train Infantry", callback_data="TROOP_TRAIN_INFANTRY"),
            InlineKeyboardButton("🛡️ Train Tanks", callback_data="TROOP_TRAIN_TANK")
        ],
        [
            InlineKeyboardButton("🎯 Train Artillery", callback_data="TROOP_TRAIN_ARTILLERY"),
            InlineKeyboardButton("💥 Train Destroyers", callback_data="TROOP_TRAIN_DESTROYER")
        ],
        [InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def troop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle troop-related callback queries."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    # Handle different troop-related callbacks
    if query.data.startswith("TROOP_TRAIN_"):
        troop_type = query.data.replace("TROOP_TRAIN_", "").lower()
        await train_troops(update, context, troop_type)
    elif query.data == "TROOP_MENU":
        await troop_menu(update, context)

async def train_troops(update: Update, context: ContextTypes.DEFAULT_TYPE, troop_type: str) -> None:
    """Handle troop training requests."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    player_data = get_player_data(query.from_user.id)
    if not player_data:
        await query.edit_message_text(
            "❌ You need to register first! Use /start to begin.",
            parse_mode=None
        )
        return
    
    # Check if barracks is high enough level for the troop type
    barracks_level = player_data.get("barracks_level", 0)
    required_level = {
        "infantry": 1,
        "tank": 5,
        "artillery": 10,
        "destroyer": 15
    }.get(troop_type, 999)
    
    if barracks_level < required_level:
        await query.edit_message_text(
            f"❌ Your Barracks needs to be level {required_level} to train {troop_type.title()}!",
            parse_mode=None
        )
        return
    
    # TODO: Implement actual training logic
    await query.edit_message_text(
        f"Training {troop_type.title()} is not implemented yet.",
        parse_mode=None
    )

def setup_troop_system(app: Application) -> None:
    """Set up the troop system handlers."""
    app.add_handler(CommandHandler("troops", troop_menu))
    app.add_handler(CallbackQueryHandler(troop_menu, pattern="^TROOP_MENU$"))
    app.add_handler(CallbackQueryHandler(troop_handler, pattern="^TROOP_")) 