# modules/registration.py
# ───────────────────────────
# Handles the /start command, prompts for in-game name,
# and registers new players into the "Players" sheet.

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

from modules.sheets_helper import (
    initialize_sheets,
    get_player_row,
    create_new_player,
    get_player_data,
    list_all_players,
)

# State for when the user is typing their in-game name
TYPING_NAME = 1

# Callback data for "Enter game name 🎮"
SET_NAME_CALLBACK = "SET_NAME"


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered by /start. If the user exists, welcome back; otherwise, prompt for name.
    """
    user = update.effective_user
    chat_id = user.id
    username = user.username or ""

    # Ensure Google Sheets is initialized
    initialize_sheets()

    # Check if user already in "Players"
    row = get_player_row(chat_id)
    if row:
        player = get_player_data(chat_id)
        game_name = player.get("game_name", "")
        # Escape the exclamation mark after game_name: "SkyHustle\!" for MarkdownV2
        await update.message.reply_text(
            f"👋 Welcome back, *{game_name}\\!* Use /base to view your empire\\.",
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
        return ConversationHandler.END

    # Not registered: send button to enter name
    keyboard = [
        [InlineKeyboardButton(text="Enter game name 🎮", callback_data=SET_NAME_CALLBACK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Escape the exclamation mark after "SkyHustle": "SkyHustle\!"
    await update.message.reply_text(
        "👋 Welcome to *SkyHustle\\!* To begin, please choose your in-game name\\:",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup,
    )
    return ConversationHandler.WAITING


async def set_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered when user clicks "Enter game name 🎮". Ask them to type their name.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Please type your desired in-game name (alphanumeric, no spaces, max 12 characters)\\."
    )
    return TYPING_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered when user sends a text message in TYPING_NAME state. Validate and register.
    """
    user = update.effective_user
    chat_id = user.id
    username = user.username or ""
    text = update.message.text.strip()

    # Validate: only letters/numbers, no spaces, ≤12 chars
    if not text.isalnum():
        await update.message.reply_text(
            "❌ Invalid name\\. Only letters and numbers allowed \\(no spaces\\)\\. Try again\\:"
        )
        return TYPING_NAME
    if len(text) > 12:
        await update.message.reply_text(
            "❌ Name too long\\. Maximum 12 characters\\. Try again\\:"
        )
        return TYPING_NAME

    # Check duplicate game_name (case-insensitive)
    for player in list_all_players():
        if player.get("game_name", "").lower() == text.lower():
            await update.message.reply_text(
                "❌ That game name is already taken\\. Please choose a different one\\:"
            )
            return TYPING_NAME

    # Register new player
    try:
        create_new_player(chat_id, username, text)
    except Exception as e:
        # Escape colon and exclamation: ":" → "\:"; "!" → "\!"
        await update.message.reply_text(
            f"⚠️ Registration failed\\: {e}\\nPlease try /start again\\."
        )
        return ConversationHandler.END

    # Fetch created data to display starting resources
    player = get_player_data(chat_id)
    resources_wood = player.get("resources_wood", 0)
    resources_stone = player.get("resources_stone", 0)
    resources_gold = player.get("resources_gold", 0)
    resources_food = player.get("resources_food", 0)

    # Escape the exclamation after "Registration complete!"
    await update.message.reply_text(
        f"✅ Registration complete\\! Your empire begins now\\.\n\n"
        f"• 🌲 Wood: {resources_wood}\n"
        f"• ⛏️ Stone: {resources_stone}\n"
        f"• 🪙 Gold: {resources_gold}\n"
        f"• 🍗 Food: {resources_food}\n\n"
        f"Use /base to check your stats\\.",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    If user sends /cancel, exit registration flow.
    """
    # Escape exclamation: "Registration canceled. Send /start when you’re ready."
    await update.message.reply_text(
        "❌ Registration canceled\\. Send /start when you’re ready\\."
    )
    return ConversationHandler.END


def setup_registration(app: Application) -> None:
    """
    Call this in main.py to register the registration conversation handler.
    """
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            ConversationHandler.WAITING: [
                CallbackQueryHandler(set_name_callback, pattern=f"^{SET_NAME_CALLBACK}$")
            ],
            TYPING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        per_user=True,
        per_chat=True,
        name="registration_conversation",
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
