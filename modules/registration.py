# modules/registration.py
# ─────────────────────────
# Full “Intro + Registration + Tutorial” flow for new players.

import datetime
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

# ───────────────────────────
# Conversation states
# ───────────────────────────
INTRO_TEXT = 0       # After /start, show the story hook
TYPING_NAME = 1      # After “Continue” clicked, user types in-game name
TUTORIAL_MENU = 2    # After registration, show “View Base” vs “How to Play”
SHOW_BASE = 3        # After clicking “View Base”
SHOW_HOWTO = 4       # While showing tutorial steps
END_TUTORIAL = 5     # After tutorial is done, return to normal

# Callback‐data identifiers
CONTINUE_CALLBACK = "INTRO_CONTINUE"
TUT_BASE_CALLBACK = "TUT_BASE"
TUT_HOWTO_CALLBACK = "TUT_HOWTO"
TUT_DONE_CALLBACK = "TUT_DONE"
SET_NAME_CALLBACK = "SET_NAME"


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered by /start. Always show the one‐time story intro—unless already registered,
    in which case we skip right to the “Welcome back” message.
    """
    user = update.effective_user
    chat_id = user.id

    # Initialize Sheets (so get_player_row() will work)
    initialize_sheets()

    # If already registered, skip intro and greet
    if get_player_row(chat_id) is not None:
        player = get_player_data(chat_id)
        game_name = player.get("game_name", "")
        await update.message.reply_text(
            f"👋 Welcome back, *{game_name}*! Use /base to jump into your empire.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # Not registered: show the very first story hook
    intro_text = (
        "🏞️ *You awaken on the edge of the Skyrealm, a land of floating isles and ancient empires.*\n\n"
        "A distant echo whispers: _“Brave one, name yourself and claim your destiny…”_\n\n"
        "👉 *Continue*"
    )
    keyboard = [[InlineKeyboardButton("👉 Continue", callback_data=CONTINUE_CALLBACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(intro_text, parse_mode="Markdown", reply_markup=reply_markup)
    return INTRO_TEXT


async def intro_continue_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    After the user clicks “Continue” on the story hook,
    prompt them for their in-game name.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Please type your desired in-game name (alphanumeric, no spaces, max 12 characters):"
    )
    return TYPING_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    User has typed a candidate in-game name. Validate it, register the player,
    then show the post-registration tutorial menu (“View Base” / “How to Play”).
    """
    user = update.effective_user
    chat_id = user.id
    username = user.username or ""
    text = update.message.text.strip()

    # 1) Validate alphanumeric, no spaces, ≤12 chars
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

    # 2) Check if game_name is already taken (case-insensitive)
    for player in list_all_players():
        if player.get("game_name", "").lower() == text.lower():
            await update.message.reply_text(
                "❌ That game name is already taken. Please choose a different one:"
            )
            return TYPING_NAME

    # 3) Register the new player
    try:
        create_new_player(chat_id, username, text)
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Registration failed: {e}\nPlease try /start again."
        )
        return ConversationHandler.END

    # 4) Show the post-registration tutorial menu
    welcome_text = (
        f"✅ *Welcome, {text}!* Your journey begins now.\n\n"
        "🔹 Your first settlement sits on fertile ground, brimming with resources.\n"
        "🔹 In SkyHustle, you’ll gather wood, stone, gold, and food to build and train troops.\n\n"
        "What would you like to do now?"
    )
    keyboard = [
        [
            InlineKeyboardButton("🏰 View My Base", callback_data=TUT_BASE_CALLBACK),
            InlineKeyboardButton("📝 How to Play", callback_data=TUT_HOWTO_CALLBACK),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    return TUTORIAL_MENU


async def tutorial_view_base(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    After the user clicks “View My Base” in the tutorial menu,
    show exactly the same output as /base does.
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    chat_id = user.id
    player = get_player_data(chat_id)

    # If somehow the player data is missing, prompt them to /start again
    if not player:
        await query.edit_message_text("❌ You aren’t registered yet. Send /start to create your empire.")
        return ConversationHandler.END

    # Build the “base overview” text
    wood = player.get("resources_wood", 0)
    stone = player.get("resources_stone", 0)
    gold = player.get("resources_gold", 0)
    food = player.get("resources_food", 0)
    diamonds = player.get("diamonds", 0)
    base_level = player.get("base_level", 1)
    game_name = player.get("game_name", "")

    base_text = (
        f"🏰 *{game_name}’s Base Overview*\n\n"
        f"• 🌲 Wood: {wood}\n"
        f"• ⛏️ Stone: {stone}\n"
        f"• 🪙 Gold: {gold}\n"
        f"• 🍗 Food: {food}\n"
        f"• 💎 Diamonds: {diamonds}\n\n"
        f"🔹 Base Level: {base_level}\n"
        f"   — Allows {min(1 + (base_level - 1) // 5, 4)} simultaneous builds\n\n"
        "Use /build to construct buildings or /train to raise troops."
    )
    await query.edit_message_text(base_text, parse_mode="Markdown")
    return END_TUTORIAL


async def tutorial_howto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    After the user clicks “How to Play,” walk them through a multi-step guide.
    We’ll show bullet points about building, training, and PvP/alliance.
    """
    query = update.callback_query
    await query.answer()

    howto_text = (
        "📝 *How to Play SkyHustle*\n\n"
        "1️⃣ *Building*\n"
        "   • Each structure (Lumber Mill, Quarry, Mine, Farm, Barracks) costs resources and time.\n"
        "   • Use `/build <structure_name>` (e.g., `/build mine`) to start an upgrade.\n\n"
        "2️⃣ *Training*\n"
        "   • Recruit soldiers at the Barracks. Each unit costs food and gold.\n"
        "   • Use `/train <unit_type> <amount>` (e.g., `/train swordsman 5`).\n\n"
        "3️⃣ *PvP & Alliances*\n"
        "   • Scout other players with `/scout <game_name>` to view their stats.\n"
        "   • Attack them with `/attack <game_name>` once you’re ready.\n"
        "   • Form alliances: `/ally invite <ally_name>`.\n\n"
        "When you’re ready, tap below to begin your journey!"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Got It, Let’s Go!", callback_data=TUT_DONE_CALLBACK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(howto_text, parse_mode="Markdown", reply_markup=reply_markup)
    return SHOW_HOWTO


async def tutorial_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    After the user clicks “Got It, Let’s Go!”, end the tutorial and let them use normal commands.
    We’ll replace the message with a small confirmation and then exit.
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎉 You’re all set! Use /base to see your empire, or explore other commands like /build and /train."
    )
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    If user sends /cancel at any point, exit the flow.
    """
    await update.message.reply_text("❌ Registration canceled. Send /start when you’re ready.")
    return ConversationHandler.END


def setup_registration(app: Application) -> None:
    """
    Call this in main.py to register the entire ConversationHandler for the intro + registration + tutorial.
    """
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            INTRO_TEXT: [
                CallbackQueryHandler(intro_continue_callback, pattern=f"^{CONTINUE_CALLBACK}$")
            ],
            TYPING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)
            ],
            TUTORIAL_MENU: [
                CallbackQueryHandler(tutorial_view_base, pattern=f"^{TUT_BASE_CALLBACK}$"),
                CallbackQueryHandler(tutorial_howto, pattern=f"^{TUT_HOWTO_CALLBACK}$"),
            ],
            SHOW_HOWTO: [
                CallbackQueryHandler(tutorial_done, pattern=f"^{TUT_DONE_CALLBACK}$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        per_user=True,
        per_chat=True,
        name="full_registration_flow",
        allow_reentry=False,  # don’t restart the intro if they type /start again mid-flow
    )

    app.add_handler(conv_handler)
