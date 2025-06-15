from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from modules.sheets_helper import (
    initialize_sheets,
    get_player_row,
    create_new_player,
    get_player_data,
    list_all_players,
)

# Conversation state
ASK_NAME = 0

# Callback data
DRAMATIC_CONTINUE = "DRAMATIC_CONTINUE"
ENTER_BASE = "ENTER_BASE"

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    # Initialize Sheets
    try:
        initialize_sheets()
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to connect to game data. Try again later.\nError: {e}"
        )
        return ConversationHandler.END

    # Returning player?
    if get_player_row(user.id) is not None:
        player = get_player_data(user.id)
        await update.message.reply_text(
            f"👋 Welcome back, *{player['game_name']}*! Use /base to view your empire.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # New player intro
    intro = (
        "🪐 *WELCOME TO SKYHUSTLE* 🪐\n"
        "The world is fractured. Factions rise. Resources are scarce.\n"
        "But YOU… you're no ordinary commander.\n\n"
        "👤 Set your *Commander Name*\n"
        "🔨 Build your base\n"
        "🛡️ Train your army\n"
        "⚔️ Dominate the zones\n"
        "💎 Rule the Black Market\n\n"
        "This is not just a game.\n"
        "It's your *empire*, your *legacy*.\n\n"
        "🎖 Ready to lead? Press below to begin."
    )
    keyboard = [[InlineKeyboardButton("🎖 Begin Your Legacy", callback_data=DRAMATIC_CONTINUE)]]
    await update.message.reply_text(intro, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ASK_NAME

async def dramatic_continue_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "✏️ Please type your desired Commander Name (alphanumeric, ≤12 chars):"
    )
    return ASK_NAME

async def received_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    name = update.message.text.strip()

    # Validate
    if not name.isalnum() or len(name) > 12:
        await update.message.reply_text(
            "❌ Invalid name—use letters/numbers only, max 12 chars. Try again:"
        )
        return ASK_NAME

    # Uniqueness check (case-insensitive)
    for p in list_all_players():
        if p.get("game_name", "").lower() == name.lower():
            await update.message.reply_text("❌ That name's taken—choose another:")
            return ASK_NAME

    # Register
    create_new_player(user.id, user.username or "", name)
    player = get_player_data(user.id)
    x, y = player["coord_x"], player["coord_y"]

    welcome = (
        f"🎉 Commander *{name}* has entered SkyHustle!\n"
        f"📍 Your base is located at X:{x}, Y:{y}\n\n"
        "🚀 Tap below to begin your conquest!"
    )
    kb = [[InlineKeyboardButton("🏠 Enter Your Base", callback_data=ENTER_BASE)]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    return ConversationHandler.END

async def enter_base_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    # Directly show base UI
    from modules.base_ui import base_handler
    await base_handler(update, context)
    return ConversationHandler.END

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Registration canceled. Send /start to retry.")
    return ConversationHandler.END

def setup_registration(app: Application) -> None:
    """
    Call this in main.py to register the registration handlers.
    """
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            ASK_NAME: [
                CallbackQueryHandler(dramatic_continue_callback, pattern=f"^{DRAMATIC_CONTINUE}$", block=False),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_name_handler, block=False),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler, block=False),
            CallbackQueryHandler(enter_base_callback, pattern=f"^{ENTER_BASE}$", block=False),
        ],
        per_user=True,
        per_chat=True,
        name="registration_flow",
        block=False,
    )
    app.add_handler(conv)


def setup_base_ui(app: Application) -> None:
    """
    Call this in main.py to register the /base command handler.
    """
    base_command = CommandHandler("base", base_handler)
    app.add_handler(base_command) 