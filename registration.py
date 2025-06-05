import os
import base64
import json
from datetime import datetime
from typing import Optional, Tuple

import gspread
from gspread import CellNotFound, WorksheetNotFound
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Conversation states
TYPING_NAME = 1

# Callback data
SET_NAME = "set_name"

# Google Sheets setup
def get_google_sheets_client() -> gspread.Client:
    """Initialize and return Google Sheets client."""
    creds_json = base64.b64decode(os.getenv("BASE64_CREDS")).decode()
    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

def ensure_players_sheet() -> gspread.Worksheet:
    """Ensure the Players worksheet exists with correct headers."""
    client = get_google_sheets_client()
    sheet = client.open_by_key(os.getenv("SHEET_ID"))
    
    try:
        worksheet = sheet.worksheet("Players")
    except WorksheetNotFound:
        worksheet = sheet.add_worksheet(
            title="Players",
            rows=1000,
            cols=10
        )
        headers = [
            "user_id", "telegram_username", "game_name", "registered_at",
            "resources_wood", "resources_stone", "resources_gold",
            "resources_food", "diamonds", "base_level"
        ]
        worksheet.append_row(headers)
    
    return worksheet

def get_player_row(user_id: int) -> Optional[int]:
    """Get the row index for a player, or None if not found."""
    worksheet = ensure_players_sheet()
    try:
        cell = worksheet.find(str(user_id))
        return cell.row
    except CellNotFound:
        return None

def create_new_player(user_id: int, username: str, game_name: str) -> None:
    """Create a new player with default resources."""
    worksheet = ensure_players_sheet()
    now = datetime.utcnow().isoformat()
    
    new_row = [
        str(user_id),
        username,
        game_name,
        now,
        "1000",  # wood
        "1000",  # stone
        "500",   # gold
        "500",   # food
        "0",     # diamonds
        "1"      # base_level
    ]
    worksheet.append_row(new_row)

def is_game_name_taken(game_name: str) -> bool:
    """Check if a game name is already taken."""
    worksheet = ensure_players_sheet()
    try:
        worksheet.find(game_name)
        return True
    except CellNotFound:
        return False

def get_player_game_name(user_id: int) -> Optional[str]:
    """Get a player's game name if they exist."""
    row = get_player_row(user_id)
    if row:
        worksheet = ensure_players_sheet()
        return worksheet.cell(row, 3).value  # game_name is in column 3
    return None

# Telegram handlers
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    if not user:
        return

    game_name = get_player_game_name(user.id)
    
    if game_name:
        # User is already registered
        await update.message.reply_text(
            f"👋 Welcome back, *{game_name}*\\! Use /base to view your empire\\.",
            parse_mode="MarkdownV2"
        )
    else:
        # New user registration
        keyboard = [[
            InlineKeyboardButton("Enter game name 🎮", callback_data=SET_NAME)
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Welcome to *SkyHustle*\\! To begin, please choose your in\\-game name:",
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )

async def set_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the SET_NAME callback."""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "✏️ Please type your desired in\\-game name \\(no spaces, max 12 characters\\):",
        parse_mode="MarkdownV2"
    )
    return TYPING_NAME

async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the game name input."""
    user = update.effective_user
    game_name = update.message.text.strip()
    
    # Validate game name
    if not game_name.isalnum():
        await update.message.reply_text(
            "❌ Game name must contain only letters and numbers\\. Please try again:",
            parse_mode="MarkdownV2"
        )
        return TYPING_NAME
    
    if len(game_name) > 12:
        await update.message.reply_text(
            "❌ Game name must be 12 characters or less\\. Please try again:",
            parse_mode="MarkdownV2"
        )
        return TYPING_NAME
    
    if is_game_name_taken(game_name):
        await update.message.reply_text(
            "❌ This game name is already taken\\. Please choose another:",
            parse_mode="MarkdownV2"
        )
        return TYPING_NAME
    
    # Create new player
    create_new_player(user.id, user.username or "unknown", game_name)
    
    # Send welcome message
    await update.message.reply_text(
        "✅ Registration complete\\! Your empire begins now\\. You start with:\n"
        "• 🌲 Wood: 1000\n"
        "• ⛰️ Stone: 1000\n"
        "• 🪙 Gold: 500\n"
        "• 🍗 Food: 500\n\n"
        "Use /base to check your stats\\.",
        parse_mode="MarkdownV2"
    )
    
    return ConversationHandler.END

def setup_registration(dispatcher) -> None:
    """Set up all registration-related handlers."""
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_handler),
            CallbackQueryHandler(set_name_callback, pattern=f"^{SET_NAME}$")
        ],
        states={
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)]
        },
        fallbacks=[],
    )
    
    dispatcher.add_handler(conv_handler) 