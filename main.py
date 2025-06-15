import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from telegram.constants import ParseMode
import time
import json
import random # For coordinates
import re

# Import our custom modules using absolute imports (as they are in the same top-level directory)
import config
from google_sheets_db_manager import GoogleSheetsDBManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def escape_markdown_v2(text: str) -> str:
    """Helper function to escape characters that have special meaning in MarkdownV2.
    This function should be applied ONLY to dynamic text that might contain
    MarkdownV2 special characters, NOT to the entire message string if it
    contains intended Markdown formatting or emojis."""
    
    # Escape backslashes first, then other special characters
    text = text.replace('\\', '\\\\')
    
    # Characters that need escaping in MarkdownV2 when they appear literally:
    # _, *, [, ], (, ), ~, `, >, #, +, -, =, |, {, }, ., !
    # Emojis do NOT need escaping.
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Initialize the database manager (singleton pattern)
db_manager = GoogleSheetsDBManager()

# --- Player State Management ---
# Using a global dictionary for player states. For persistent state across bot restarts
# in a production environment, consider using a database or context.user_data with persistence.
player_states = {} # {user_id: "state_name"}

# --- Helper Functions ---

def generate_random_coordinates():
    """Generates random coordinates for a new player within a reasonable map size."""
    x = random.randint(1, 1000) # Example range
    y = random.randint(1, 1000)
    return x, y

async def send_base_ui(update: Update, context: ContextTypes.DEFAULT_TYPE, player_data: dict):
    """Sends the main Base UI to the user, reflecting their current game state.
    Uses MarkdownV2 for formatting, with careful escaping for dynamic content and literal punctuation."""

    current_timestamp = int(time.time())
    
    last_login_ts = 0
    if 'last_login_timestamp' in player_data and player_data['last_login_timestamp']:
        try:
            last_login_ts = int(player_data['last_login_timestamp'])
        except ValueError:
            logger.warning(f"Invalid last_login_timestamp for {player_data['user_id']}: {player_data['last_login_timestamp']}")
            last_login_ts = 0 

    updates_to_db = {}
    if current_timestamp > last_login_ts:
        time_offline_seconds = current_timestamp - last_login_ts
        logger.info(f"Player {player_data['commander_name']} was offline for {time_offline_seconds} seconds.")
    
    updates_to_db["last_login_timestamp"] = str(current_timestamp)

    db_manager.update_player_data(player_data['user_id'], updates_to_db)
    player_data.update(updates_to_db)

    # Prepare resource string for UI with specific escaping
    resources_display = []
    for res_type in config.STARTING_RESOURCES.keys():
        current_amount = player_data['current_resources'].get(res_type, 0)
        cap_amount = player_data['resource_caps'].get(res_type, 0)
        if res_type == 'diamonds':
            resources_display.append(f"💎 Diamonds: {escape_markdown_v2(str(current_amount))}")
        else:
            resources_display.append(f"{res_type.capitalize()}: {escape_markdown_v2(str(current_amount))}/{escape_markdown_v2(str(cap_amount))}")
    resources_str = "\n".join(resources_display)

    # Prepare building levels string for UI with specific escaping
    building_levels_str = "\n".join([
        f"{b.replace('_', ' ').title()}: Lv {escape_markdown_v2(str(player_data['building_levels'].get(b, 0)))}"
        for b in config.INITIAL_BUILDING_LEVELS.keys()
    ])

    # Define separator line with escaped underscores
    separator = escape_markdown_v2("___")

    # Construct main message text with careful MarkdownV2 and escaping
    # Emojis directly inserted. Bolding done with literal *.
    # Punctuation like ':', ',', '.', '!' are escaped if they are literal.
    message_text = (
        f"🏠 *{escape_markdown_v2(player_data['commander_name'])}*{escape_markdown_v2('\'s')} Base\n"
        f"🏅 Power{escape_markdown_v2(':')} {escape_markdown_v2(str(player_data['player_power']))}\n"
        f"📍 Coords{escape_markdown_v2(':')} X{escape_markdown_v2(':')}*{escape_markdown_v2(str(player_data['coordinates_x']))}*{escape_markdown_v2(',')} "
        f"Y{escape_markdown_v2(':')}*{escape_markdown_v2(str(player_data['coordinates_y']))}*\n"
        f"{separator}\n"
        f"💰 *Resources{escape_markdown_v2(':')}*\n{resources_str}\n"
        f"{separator}\n"
        f"🧱 *Buildings{escape_markdown_v2(':')}*\n{building_levels_str}\n"
        f"{separator}\n"
        f"🎯 *Main Actions{escape_markdown_v2(':')}*\n"
    )

    keyboard = [
        [InlineKeyboardButton("⚒️ Build", callback_data="build_menu")],
        [InlineKeyboardButton("🧪 Research", callback_data="research_menu")],
        [InlineKeyboardButton("🪖 Train", callback_data="train_menu")],
        [InlineKeyboardButton("⚔️ Attack", callback_data="attack_menu")],
        [InlineKeyboardButton("🤝 Alliance", callback_data="alliance_menu")],
        [InlineKeyboardButton("🏪 Shop", callback_data="shop_menu")],
        [InlineKeyboardButton("🧭 Scout", callback_data="scout_menu")],
        [InlineKeyboardButton("⚙️ Strategy", callback_data="strategy_menu")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile_menu")],
        [InlineKeyboardButton("✉️ Inbox", callback_data="inbox_menu")],
        [InlineKeyboardButton("🎖 Quests", callback_data="quests_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await update.effective_chat.send_message(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    player_states[player_data['user_id']] = "base_view"


# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command. Registers new players or shows base to existing ones."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    logger.info(f"User {user_id} (username: {username}, first_name: {first_name}) used /start.")

    player_data = db_manager.get_player_data(user_id)

    if player_data:
        # Existing user
        player_states[user_id] = 'main_menu' # Set state using global dict
        last_login_timestamp = int(player_data.get('last_login_timestamp', 0))
        current_timestamp = int(time.time())
        offline_duration = current_timestamp - last_login_timestamp
        
        player_data['last_login_timestamp'] = str(current_timestamp) # Ensure it's stored as string
        db_manager.update_player_data(user_id, player_data)
        logger.info(f"Player {player_data['commander_name']} was offline for {offline_duration} seconds.")

        # Construct welcome message for existing user with careful MarkdownV2 and escaping
        welcome_message = (
            f"Welcome back, Commander *{escape_markdown_v2(player_data['commander_name'])}*{escape_markdown_v2('!')}\n"
            f"You were offline for {escape_markdown_v2(str(offline_duration))} seconds{escape_markdown_v2('.')} "
            f"What{escape_markdown_v2('\'s')} your next move{escape_markdown_v2('?')}"
        )
        
        await update.message.reply_text(
            text=welcome_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Enter Your Base", callback_data='enter_your_base')]
            ])
        )
    else:
        # New user registration
        player_states[user_id] = 'awaiting_initial_name_action' # Set state using global dict
        
        # Static message for new users - emojis are literal, use * for bold, escape other punctuation
        welcome_message = (
            f"🪐 *WELCOME TO SKYHUSTLE* 🪐\n"
            f"The world is fractured{escape_markdown_v2('.')} Factions rise{escape_markdown_v2('.')} Resources are scarce{escape_markdown_v2('.')}\n"
            f"But YOU{escape_markdown_v2('…')} you{escape_markdown_v2('\'re')} no ordinary commander{escape_markdown_v2('.')}\n"
            f"👤 Set your *Commander Name*\n"
            f"🔨 Build your base\n"
            f"️ Train your army\n"
            f"⚔️ Dominate the zones\n"
            f"💎 Rule the Black Market\n"
            f"This is not just a game{escape_markdown_v2('.')}\n"
            f"It{escape_markdown_v2('\'s')} your *empire*{escape_markdown_v2('.')} Your *legacy*{escape_markdown_v2('.')}\n"
            f"🎖 Ready to lead{escape_markdown_v2('?')}"
        )
        
        await update.message.reply_text(
            text=welcome_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Set Commander Name", callback_data='set_commander_name')]
            ]),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"New user {user_id} ({first_name}) started the bot. Initiating registration.")


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_state = player_states.get(user_id)
    callback_data = query.data

    logger.info(f"User {user_id} current state: {user_state}, Callback Data: {callback_data}")

    if callback_data == "set_commander_name" and user_state == "awaiting_initial_name_action":
        await query.edit_message_text(
            text="Alright, Commander! What name shall history remember you by?\n\n"
                 "*(Min 3 characters, Max 15, alphanumeric only)*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        player_states[user_id] = "awaiting_commander_name_input"
        return

    if callback_data == 'enter_your_base':
        player_data = db_manager.get_player_data(user_id)
        if player_data:
            await send_base_ui(update, context, player_data)
            player_states[user_id] = 'base_view'
        else:
            await query.edit_message_text(
                text=escape_markdown_v2("It seems you're not registered yet! Please use /start to begin your journey."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            player_states.pop(user_id, None)
        return

    elif callback_data == "build_menu":
        await query.edit_message_text(
            text=f"⚒️ You are in the Build Menu{escape_markdown_v2('!')} (Coming soon{escape_markdown_v2('...')})",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        player_states[user_id] = "build_view"
        await query.message.reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back to Base", callback_data="back_to_base")]]))
    
    elif callback_data == "train_menu":
        await query.edit_message_text(
            text=f"🪖 You are in the Train Menu{escape_markdown_v2('!')} (Coming soon{escape_markdown_v2('...')})",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        player_states[user_id] = "train_view"
        await query.message.reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back to Base", callback_data="back_to_base")]]))
    
    elif callback_data == "back_to_base":
        player_data = db_manager.get_player_data(user_id)
        if player_data:
            await send_base_ui(update, context, player_data)
        else:
            await query.edit_message_text(
                text=escape_markdown_v2("Error: Player data not found. Please try /start again."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            player_states.pop(user_id, None)
    
    else:
        logger.warning(f"Unhandled callback '{callback_data}' in state '{user_state}' for user {user_id}")
        await query.edit_message_text(
            text=escape_markdown_v2("Sorry, I don't understand that action right now. Please use the available buttons or type /start."),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        player_states.pop(user_id, None)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages from the user."""
    user_id = update.effective_user.id
    user_message = update.message.text
    current_state = player_states.get(user_id) # Get state from global dict

    logger.info(f"User {user_id} current state: {current_state}, Message: '{user_message}'")

    if current_state == "awaiting_commander_name_input":
        commander_name = user_message.strip()

        # Validate Commander Name (Min 3, Max 15, Alpha-numeric)
        if not (3 <= len(commander_name) <= 15 and commander_name.isalnum()):
            await update.message.reply_text(
                text=escape_markdown_v2("⚠️ Invalid name. Name must be 3-15 alpha-numeric characters.\nPlease try again:"),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return

        # Check for uniqueness (case-insensitive for uniqueness check)
        all_players = db_manager.get_all_players()
        if any(p.get('commander_name', '').lower() == commander_name.lower() for p in all_players):
            await update.message.reply_text(
                text=f"⚠️ Commander Name '*{escape_markdown_v2(commander_name)}*' is already taken{escape_markdown_v2('.')}\nPlease choose another{escape_markdown_v2(':')}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return

        # Create new player data
        x_coord, y_coord = generate_random_coordinates()
        new_player_data = {
            "user_id": str(user_id), # Store as string in Google Sheets
            "commander_name": commander_name,
            "coordinates_x": str(x_coord), # Store as string
            "coordinates_y": str(y_coord), # Store as string
            "current_resources": config.STARTING_RESOURCES,
            "resource_caps": config.INITIAL_RESOURCE_CAPS,
            "building_levels": config.INITIAL_BUILDING_LEVELS,
            "unit_counts": config.INITIAL_UNIT_COUNTS,
            "player_power": "100", # Initial power, will be calculated dynamically later
            "prestige_level": "0",
            "last_login_timestamp": "0", # Will be updated on first base load
            "active_hero_assignments": {},
            "owned_heroes": {},
            "captured_heroes": {},
            "active_timers": {},
            "alliance_id": "none", # No alliance initially
            "peace_shield_end_timestamp": "0", # No peace shield initially
            "strategy_points_available": "0",
            "strategy_point_allocations": {},
            "completed_research": [],
            "quest_progress": {},
        }

        if db_manager.create_player(new_player_data):
            keyboard = [[InlineKeyboardButton("🏠 Enter Your Base", callback_data="enter_your_base")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text=f"🎉 Commander *{escape_markdown_v2(commander_name)}* has entered SkyHustle{escape_markdown_v2('!')}\n"
                     f"📍 Your base is located at *X:{escape_markdown_v2(str(x_coord))}*{escape_markdown_v2(',')} Y:*{escape_markdown_v2(str(y_coord))}*\n"
                     f"🚀 Tap below to begin your conquest{escape_markdown_v2('!')}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            player_states[user_id] = "registration_complete"
        else:
            await update.message.reply_text(
                text=escape_markdown_v2("🚫 An error occurred during registration. Please try /start again."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            player_states.pop(user_id, None) # Clear state on error
    elif current_state == "base_view":
        await update.message.reply_text(
            text=escape_markdown_v2("Please use the buttons for actions, Commander! Or type /help."),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            text=escape_markdown_v2("I'm not sure how to respond to that right now. Please use the buttons or try /start."),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        player_states.pop(user_id, None)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text(
        text=escape_markdown_v2("Use /start to begin or return to your base. Use the inline buttons for actions!"),
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update.effective_message:
        await update.effective_message.reply_text(
            text=escape_markdown_v2("An unexpected error occurred! Please try again or type /start."),
            parse_mode=ParseMode.MARKDOWN_V2
        )

def main() -> None:
    """Start the bot."""
    if not all([config.TELEGRAM_BOT_TOKEN, config.GOOGLE_SHEET_ID, config.GOOGLE_CREDENTIALS_JSON_CONTENT]):
        logger.error("Missing one or more required environment variables (TELEGRAM_BOT_TOKEN, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_JSON). Please set them on Render.")
        return

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.add_error_handler(error_handler)

    logger.info("SkyHustle bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()