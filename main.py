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
    """Helper function to escape characters that have special meaning in MarkdownV2."""
    text = text.replace('\\', '\\\\') # Escape backslashes first
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Initialize the database manager (singleton pattern)
db_manager = GoogleSheetsDBManager()

# --- Player State Management ---
# This dictionary will temporarily hold player states for multi-step interactions.
# In a distributed environment or if the bot restarts frequently, this should be
# moved to a more persistent store (e.g., a dedicated Redis cache or directly in the DB).
# For now, in-memory is sufficient for a basic bot on Render.
player_states = {} # {user_id: "state_name"}

# --- Helper Functions ---

def generate_random_coordinates():
    """Generates random coordinates for a new player within a reasonable map size."""
    x = random.randint(1, 1000) # Example range
    y = random.randint(1, 1000)
    return x, y

async def send_base_ui(update: Update, context: ContextTypes.DEFAULT_TYPE, player_data: dict):
    """Sends the main Base UI to the user, reflecting their current game state."""
    # This function will be expanded significantly in later phases
    # For now, it shows resources, building levels, and main action buttons.

    # --- Offline Progression Calculation (simplified for now) ---
    # This is a placeholder. A full system would calculate resources generated offline
    # and complete any timers that finished.
    current_timestamp = int(time.time())
    
    # Ensure last_login_timestamp is parsed correctly, it might be a string from Google Sheets
    last_login_ts = 0
    if 'last_login_timestamp' in player_data and player_data['last_login_timestamp']:
        try:
            last_login_ts = int(player_data['last_login_timestamp'])
        except ValueError:
            logger.warning(f"Invalid last_login_timestamp for {player_data['user_id']}: {player_data['last_login_timestamp']}")
            last_login_ts = 0 # Reset to 0 if invalid

    updates_to_db = {}
    if current_timestamp > last_login_ts:
        time_offline_seconds = current_timestamp - last_login_ts
        logger.info(f"Player {player_data['commander_name']} was offline for {time_offline_seconds} seconds.")
        # Future: Call a dedicated function to calculate offline resource gains and timer completions
        # For now, just logging.
    
    updates_to_db["last_login_timestamp"] = str(current_timestamp) # Always update timestamp on base view

    # Apply updates to DB
    db_manager.update_player_data(player_data['user_id'], updates_to_db)
    # Also update the in-memory player_data dict
    player_data.update(updates_to_db)

    # Prepare resource string for UI
    resources_display = []
    # Loop through resources defined in config, ensuring all are displayed
    for res_type in config.STARTING_RESOURCES.keys():
        current_amount = player_data['current_resources'].get(res_type, 0)
        cap_amount = player_data['resource_caps'].get(res_type, 0)
        if res_type == 'diamonds': # Diamonds usually don't have a cap
            resources_display.append(f"💎 Diamonds: {escape_markdown_v2(str(current_amount))}")
        else:
            resources_display.append(f"{res_type.capitalize()}: {escape_markdown_v2(str(current_amount))}/{escape_markdown_v2(str(cap_amount))}")
    resources_str = "\n".join(resources_display)

    # Prepare building levels string for UI
    building_levels_str = "\n".join([
        f"{b.replace('_', ' ').title()}: Lv {escape_markdown_v2(str(player_data['building_levels'].get(b, 0)))}"
        for b in config.INITIAL_BUILDING_LEVELS.keys()
    ])

    # Construct message with proper MarkdownV2 formatting and escaping
    message_text = (
        f"🏠 Commander *{escape_markdown_v2(player_data['commander_name'])}*{escape_markdown_v2("'s")} Base\n"
        f"🏅 Power: {escape_markdown_v2(str(player_data['player_power']))}\n"
        f"📍 Coords: X:*{escape_markdown_v2(str(player_data['coordinates_x']))}*{escape_markdown_v2(',')} "
        f"Y:*{escape_markdown_v2(str(player_data['coordinates_y']))}*\n"
        f"___\n"
        f"💰 *Resources:*\n{resources_str}\n"
        f"___\n"
        f"🧱 *Buildings:*\n{building_levels_str}\n"
        f"___\n"
        f"🎯 *Main Actions:*\n"
    )

    keyboard = [
        [InlineKeyboardButton("⚒️ Build", callback_data="build_menu")],
        [InlineKeyboardButton("🧪 Research", callback_data="research_menu")], # Placeholder
        [InlineKeyboardButton("🪖 Train", callback_data="train_menu")],
        [InlineKeyboardButton("⚔️ Attack", callback_data="attack_menu")], # Placeholder
        [InlineKeyboardButton("🤝 Alliance", callback_data="alliance_menu")], # Placeholder
        [InlineKeyboardButton("🏪 Shop", callback_data="shop_menu")], # Placeholder
        [InlineKeyboardButton("🧭 Scout", callback_data="scout_menu")], # Placeholder
        [InlineKeyboardButton("⚙️ Strategy", callback_data="strategy_menu")], # Placeholder
        [InlineKeyboardButton("👤 Profile", callback_data="profile_menu")], # Placeholder
        [InlineKeyboardButton("✉️ Inbox", callback_data="inbox_menu")], # Placeholder
        [InlineKeyboardButton("🎖 Quests", callback_data="quests_menu")], # Placeholder
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use query.edit_message_text if updating an existing message,
    # otherwise use update.effective_chat.send_message
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
        context.user_data['state'] = 'main_menu'
        last_login_timestamp = player_data.get('last_login_timestamp', 0)
        current_timestamp = int(time.time())
        offline_duration = current_timestamp - last_login_timestamp
        
        player_data['last_login_timestamp'] = current_timestamp
        db_manager.update_player_data(user_id, player_data)
        logger.info(f"Player {player_data['commander_name']} was offline for {offline_duration} seconds.")

        # Escape only the dynamic commander_name and duration value.
        # Manually add '*' for bolding.
        # Manually escape static punctuation like '!', '.' for literal display.
        welcome_message = (
            f"Welcome back, Commander *{escape_markdown_v2(player_data['commander_name'])}*{escape_markdown_v2('!')}\n"
            f"You were offline for {escape_markdown_v2(str(offline_duration))} seconds{escape_markdown_v2('.')}"
            f" What's your next move{escape_markdown_v2('?')}"
        )
        
        await update.message.reply_text(
            text=welcome_message, # Use the carefully constructed message
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Enter Your Base", callback_data='enter_your_base')]
            ])
        )
    else:
        # New user registration
        context.user_data['state'] = 'awaiting_initial_name_action'
        
        welcome_message = escape_markdown_v2( # This escapes the static '!' in the new user message
            "Welcome, brave Commander! Your journey in SkyHustle begins now.\n\n"
            "To get started, first you need to set your Commander name."
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
    await query.answer() # Always answer the callback query

    user_id = update.effective_user.id
    user_state = context.user_data.get('state')
    callback_data = query.data

    logger.info(f"User {user_id} current state: {user_state}, Callback Data: {callback_data}")

    # Handle 'set_commander_name' (Existing logic remains)
    if callback_data == 'set_commander_name' and user_state == 'awaiting_initial_name_action':
        # ... (your existing code for handling set_commander_name) ...
        context.user_data['state'] = 'awaiting_commander_name_input'
        await query.edit_message_text(text="Alright, Commander! What name shall history remember you by?\n\n"
                                          "*(Min 3 characters, Max 15, alphanumeric only)*")
        return

    # --- NEW / MODIFIED LOGIC FOR 'enter_your_base' ---
    if callback_data == 'enter_your_base':
        player_data = db_manager.get_player_data(user_id)
        if player_data:
            # Player is registered, so show them their base
            await send_base_ui(update, context, player_data)
            context.user_data['state'] = 'base_view' # Set state after entering base
        else:
            # Player somehow clicked 'enter_your_base' but isn't registered.
            # Redirect them to the start command.
            await query.edit_message_text(text="It seems you're not registered yet! Please use /start to begin your journey.")
            context.user_data['state'] = None # Reset state
        return

    # If you have other callbacks, ensure they are handled with appropriate state checks.
    logger.warning(f"Unhandled callback '{callback_data}' in state '{user_state}' for user {user_id}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages from the user."""
    user_id = update.effective_user.id
    user_message = update.message.text
    current_state = player_states.get(user_id)

    logger.info(f"User {user_id} current state: {current_state}, Message: '{user_message}'")

    if current_state == "awaiting_commander_name_input":
        commander_name = user_message.strip()

        # Validate Commander Name (Min 3, Max 15, Alpha-numeric)
        if not (3 <= len(commander_name) <= 15 and commander_name.isalnum()):
            await update.message.reply_text(
                "⚠️ Invalid name. Name must be 3-15 alpha-numeric characters.\nPlease try again:"
            )
            return

        # Check for uniqueness (case-insensitive for uniqueness check)
        all_players = db_manager.get_all_players()
        if any(p.get('commander_name', '').lower() == commander_name.lower() for p in all_players):
            await update.message.reply_text(
                f"⚠️ Commander Name '{commander_name}' is already taken.\nPlease choose another:"
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
                f"🎉 Commander *{commander_name}* has entered SkyHustle!\n"
                f"📍 Your base is located at *X:{x_coord}, Y:{y_coord}*\n"
                "🚀 Tap below to begin your conquest!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            player_states[user_id] = "registration_complete"
        else:
            await update.message.reply_text("🚫 An error occurred during registration. Please try /start again.")
            player_states.pop(user_id, None) # Clear state on error
    elif current_state == "base_view":
        # General response if user types something while in base_view state
        await update.message.reply_text("Please use the buttons for actions, Commander! Or type /help.")
    # Add more message handlers based on player_states as needed for future features
    else:
        # Default fallback for unhandled text messages
        await update.message.reply_text("I'm not sure how to respond to that right now. Please use the buttons or try /start.")
        player_states.pop(user_id, None) # Clear state if no clear path


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text("Use /start to begin or return to your base. Use the inline buttons for actions!")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update.effective_message:
        await update.effective_message.reply_text("An unexpected error occurred! Please try again or type /start.")

def main() -> None:
    """Start the bot."""
    # Ensure all required environment variables are set
    if not all([config.TELEGRAM_BOT_TOKEN, config.GOOGLE_SHEET_ID, config.GOOGLE_CREDENTIALS_JSON_CONTENT]):
        logger.error("Missing one or more required environment variables (TELEGRAM_BOT_TOKEN, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_JSON). Please set them on Render.")
        # In a production setup, you might want to raise an exception or exit here.
        # For now, just log the error. The bot will likely fail to authorize with Telegram or Google Sheets.
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)) # Handles all non-command text messages

    # Log all errors
    application.add_error_handler(error_handler)

    logger.info("SkyHustle bot started polling...")
    # Run the bot until the user presses Ctrl-C (or until Render stops the service)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main() 