# modules/registration.py

import os
import datetime

from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

from modules.sheets_helper import initialize_sheets, get_player_row, create_new_player, get_player_data

# Conversation state for entering a new game name
TYPING_NAME = 1

# Callback data identifier for “Enter game name” button
SET_NAME_CALLBACK = "SET_NAME"


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    This handler is triggered when the user sends /start.
    If they’re already registered, greet them.
    If not, prompt them to set their in-game name.
    """
    user = update.effective_user
    chat_id = user.id
    username = user.username or ""  # May be empty if user has no @username

    # Ensure Sheets are initialized (in case main.py forgot to call initialize_sheets())
    initialize_sheets()

    # Check if user already exists in “Players”
    row = get_player_row(chat_id)
    if row:
        # Already registered
        player = get_player_data(chat_id)
        game_name = player.get("game_name", "")
        await update.message.reply_text(
            f"👋 Welcome back, *{game_name}*! Use /base to view your empire.",
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
        return ConversationHandler.END

    # Not registered yet: prompt for in-game name
    keyboard = [
        [InlineKeyboardButton(text="Enter game name 🎮", callback_data=SET_NAME_CALLBACK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to *SkyHustle*! To begin, please choose your in-game name:",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup,
    )
    return ConversationHandler.WAITING


async def set_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered when the user clicks “Enter game name 🎮” button.
    Ask them to type their desired name.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    await query.edit_message_text(
        "✏️ Please type your desired in-game name (alphanumeric, no spaces, max 12 characters):"
    )
    return TYPING_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered when the user types a text message while in the TYPING_NAME state.
    Validate the name, create the player if valid, or re-prompt if invalid.
    """
    user = update.effective_user
    chat_id = user.id
    username = user.username or ""
    text = update.message.text.strip()

    # Validation: alphanumeric, no spaces, length ≤ 12
    if not text.isalnum():
        await update.message.reply_text(
            "❌ Invalid name. Only letters and numbers allowed (no spaces). Try again:"
        )
        return TYPING_NAME

    if len(text) > 12:
        await update.message.reply_text(
            "❌ Name too long. Maximum 12 characters. Try again:"
        )
        return TYPING_NAME

    # Check for duplicate game_name
    # We'll fetch all players and compare names case-insensitively
    all_players = get_player_data(chat_id)  # current user is not yet registered
    # Instead, iterate sheet manually:
    from modules.sheets_helper import list_all_players

    for player in list_all_players():
        if player.get("game_name", "").lower() == text.lower():
            await update.message.reply_text(
                "❌ That game name is already taken. Please choose a different one:"
            )
            return TYPING_NAME

    # All good—create new player
    try:
        create_new_player(chat_id, username, text)
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Failed to register new player: {e}\nPlease try /start again."
        )
        return ConversationHandler.END

    # Fetch newly created data to display starting resources
    player = get_player_data(chat_id)
    resources_wood = player.get("resources_wood", 0)
    resources_stone = player.get("resources_stone", 0)
    resources_gold = player.get("resources_gold", 0)
    resources_food = player.get("resources_food", 0)

    await update.message.reply_text(
        f"✅ Registration complete! Your empire begins now.\n\n"
        f"• 🌲 Wood: {resources_wood}\n"
        f"• ⛏️ Stone: {resources_stone}\n"
        f"• 🪙 Gold: {resources_gold}\n"
        f"• 🍗 Food: {resources_food}\n\n"
        f"Use /base to check your stats.",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    If at any point the user wants to cancel (e.g., types /cancel), exit the flow.
    """
    await update.message.reply_text("❌ Registration canceled. Send /start when you’re ready.")
    return ConversationHandler.END


def setup_registration(app: Application) -> None:
    """
    Call this in main.py to register all handlers related to user registration.
    """
    # Conversation handler for /start → set name → receive name
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            ConversationHandler.WAITING: [CallbackQueryHandler(set_name_callback, pattern=f"^{SET_NAME_CALLBACK}$")],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        per_user=True,
        per_chat=True,
        name="registration_conversation",
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
