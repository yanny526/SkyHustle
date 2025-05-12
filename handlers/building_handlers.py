"""
Building related command handlers for the SkyHustle Telegram bot.
These handlers manage construction and management of player buildings.
"""
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from modules.player import get_player
from modules.building import get_buildings, add_building_to_queue
from utils.formatter import format_error, format_success, format_building_info

logger = logging.getLogger(__name__)

def build(update: Update, context: CallbackContext):
    """Handler for /build command - allows player to construct buildings."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    # If no arguments provided, show building options
    if not context.args or len(context.args) < 1:
        show_building_options(update, context)
        return
    
    # Parse arguments
    building_id = context.args[0].lower()
    quantity = 1
    if len(context.args) > 1:
        try:
            quantity = int(context.args[1])
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            update.message.reply_text(
                format_error("Invalid quantity. Please provide a positive number.")
            )
            return
    
    # Attempt to add building to construction queue
    result = add_building_to_queue(user.id, building_id, quantity)
    
    if result['success']:
        update.message.reply_text(
            format_success(f"Added {quantity}x {result['building_name']} to construction queue!")
        )
    else:
        update.message.reply_text(
            format_error(result['message'])
        )

def show_building_options(update: Update, context: CallbackContext):
    """Shows available buildings as inline keyboard buttons."""
    buildings = get_buildings()
    
    # Group buildings by category
    categories = {}
    for b in buildings:
        if b['category'] not in categories:
            categories[b['category']] = []
        categories[b['category']].append(b)
    
    message_text = "*Available Buildings:*\n\nSelect a building to construct:"
    
    # Create a keyboard with buttons for each building category
    keyboard = []
    for category, buildings_list in categories.items():
        row = []
        for building in buildings_list[:3]:  # Limit to 3 buildings per row
            button = InlineKeyboardButton(
                building['name'], 
                callback_data=json.dumps({"cmd": "build", "id": building['id']})
            )
            row.append(button)
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )

def handle_build_callback(update: Update, context: CallbackContext, building_id: str):
    """Handles selection of a building from the inline keyboard."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get building details
    buildings = get_buildings()
    selected_building = next((b for b in buildings if b['id'] == building_id), None)
    
    if not selected_building:
        query.edit_message_text(format_error("Building not found."))
        return
    
    # Format building info message
    building_info = format_building_info(selected_building)
    
    # Add confirm/cancel buttons
    keyboard = [
        [
            InlineKeyboardButton(
                "Build 1", 
                callback_data=json.dumps({"cmd": "build_confirm", "id": building_id, "qty": 1})
            ),
            InlineKeyboardButton(
                "Build 5", 
                callback_data=json.dumps({"cmd": "build_confirm", "id": building_id, "qty": 5})
            )
        ],
        [
            InlineKeyboardButton(
                "Back to Buildings", 
                callback_data=json.dumps({"cmd": "build_menu"})
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        building_info,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )

def defensive(update: Update, context: CallbackContext):
    """Handler for /defensive command - manages defensive structures."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    # In a full implementation, this would show defensive structures and settings
    update.message.reply_text(
        format_error("Defensive structure management coming soon!")
    )
