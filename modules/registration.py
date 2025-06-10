from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application
)
from modules.sheets_helper import initialize_sheets, get_player_row, create_new_player, get_player_data, list_all_players
from modules.base_ui import base_handler

# Conversation states
ASK_NAME = 0

# Callback data
DRAMATIC_CONTINUE = "dramatic_continue"
ENTER_BASE = "enter_base"

# Helper to check if game name is taken
def _is_game_name_taken(game_name: str) -> bool:
    """Checks if a game name is already taken by another player."""
    all_players = list_all_players()
    for player in all_players:
        if player.get("game_name", "") == game_name:
            return True
    return False


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /start command, initiating registration or welcoming back a player."""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Something went wrong\\. Please try again\\.", parse_mode=constants.ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    # Ensure sheets are initialized (defensive check)
    try:
        initialize_sheets()
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to connect to game data\\. Please try again later\\. Error: {e}", parse_mode=constants.ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    if get_player_row(user.id) is not None:
        player_data = get_player_data(user.id)
        game_name = player_data.get("game_name", "Commander")
        await update.message.reply_text(
            f"👋 Welcome back, \*{game_name}\*\\! Use /base to view your empire\\.",
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END
    else:
        # New user flow
        text = (
            "🪐 \*WELCOME TO SKYHUSTLE\* 🪐\n"
            "The world is fractured… but YOU are no ordinary commander\\.\n"
            "👤 Set your \*Commander Name\*\\n"
            "🔨 Build your base\\n"
            "🛡️ Train your army\\n"
            "⚔️ Dominate the zones\\n"
            "💎 Rule the Black Market\\n\\n"
            "🎖 Ready to lead\\? Press below\\."
        )
        keyboard = [[InlineKeyboardButton("🎖 Begin Your Legacy", callback_data=DRAMATIC_CONTINUE)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2, reply_markup=reply_markup
        )
        return ASK_NAME # Stay in conversation state for the next input (callback query)


async def dramatic_continue_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the callback from the 'Begin Your Legacy' button, prompting for name input."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "✏️ Please type your desired Commander Name \\(alphanumeric, no spaces, max 12 chars\\):",
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )
    return ASK_NAME


async def received_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's commander name input, validates it, and registers the player."""
    user = update.effective_user
    game_name = update.message.text.strip()
    chat_id = user.id
    username = user.username or ""

    # 1. Validate name format
    if not game_name.isalnum():
        await update.message.reply_text(
            "❌ Commander Name must contain only letters and numbers\\. Please try again:",
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return ASK_NAME
    
    if len(game_name) > 12:
        await update.message.reply_text(
            "❌ Commander Name must be 12 characters or less\\. Please try again:",
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return ASK_NAME
    
    # 2. Check uniqueness
    try:
        if _is_game_name_taken(game_name):
            await update.message.reply_text(
                "❌ This Commander Name is already taken\\. Please choose another:",
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
            return ASK_NAME
    except Exception as e:
        await update.message.reply_text(f"❗ Error checking name uniqueness: {e}\\ . Please try again later\\.", parse_mode=constants.ParseMode.MARKDOWN_V2)
        return ConversationHandler.END # End on critical error

    # 3. Create new player
    try:
        create_new_player(chat_id, username, game_name)
        player_data = get_player_data(chat_id)
        coord_x = player_data.get("coord_x", 0)
        coord_y = player_data.get("coord_y", 0)

        text = (
            f"🎉 Commander \*{game_name}\* has entered SkyHustle\\!\\n"
            f"📍 Your base is located at \*X:{coord_x}, Y:{coord_y}\*\\n\\n"
            f"🚀 Tap below to begin your conquest\\!"
        )
        keyboard = [[InlineKeyboardButton("🏠 Enter Your Base", callback_data=ENTER_BASE)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2, reply_markup=reply_markup
        )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to register your empire: {e}\\ . Please try again later\\.", parse_mode=constants.ParseMode.MARKDOWN_V2)
        return ConversationHandler.END


async def enter_base_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the callback from the 'Enter Your Base' button."""
    query = update.callback_query
    await query.answer()
    await base_handler(update, context)
    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation flow."""
    await update.message.reply_text("Registration cancelled\\.", parse_mode=constants.ParseMode.MARKDOWN_V2)
    return ConversationHandler.END


def setup_registration(app: Application) -> None:
    """Sets up all registration-related handlers and adds them to the application."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            ASK_NAME: [
                CallbackQueryHandler(dramatic_continue_callback, pattern=f"^{DRAMATIC_CONTINUE}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_name_handler),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CallbackQueryHandler(enter_base_callback, pattern=f"^{ENTER_BASE}$")
        ],
    )
    app.add_handler(conv_handler)


def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    base_command = CommandHandler("base", base_handler)
    app.add_handler(base_command) 