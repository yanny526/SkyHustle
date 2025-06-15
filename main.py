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
import time
import json
import random # For coordinates

# Import our custom modules using absolute imports
import config
from google_sheets_db_manager import GoogleSheetsDBManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
            resources_display.append(f"💎 Diamonds: {current_amount}")
        else:
            resources_display.append(f"{res_type.capitalize()}: {current_amount}/{cap_amount}")
    resources_str = "\n".join(resources_display)

    # Prepare building levels string for UI
    building_levels_str = "\n".join([
        f"{b.replace('_', ' ').title()}: Lv {player_data['building_levels'].get(b, 0)}"
        for b in config.INITIAL_BUILDING_LEVELS.keys()
    ])

    message_text = (
        f"🏠 *{player_data['commander_name']}'s Base*\n"
        f"🏅 Power: {player_data['player_power']}\n"
        f"📍 Coords: X:{player_data['coordinates_x']}, Y:{player_data['coordinates_y']}\n"
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
            parse_mode='Markdown'
        )
    else:
        await update.effective_chat.send_message(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    player_states[player_data['user_id']] = "base_view"


# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command. Registers new players or shows base to existing ones."""
    user_id = update.effective_user.id
    commander_name = update.effective_user.username # Use username as initial commander name suggestion, might be None

    # Retrieve player data from DB
    player_data = db_manager.get_player_data(user_id)

    if player_data is None:
        # New player registration flow
        logger.info(f"New user {user_id} ({commander_name}) started the bot. Initiating registration.")
        keyboard = [[InlineKeyboardButton("Set Commander Name", callback_data="set_commander_name")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🪐 *WELCOME TO SKYHUSTLE* 🪐\n"
            "The world is fractured. Factions rise. Resources are scarce.\n"
            "But YOU… you're no ordinary commander.\n"
            "👤 Set your *Commander Name*\n"
            "🔨 Build your base\n"
            "️ Train your army\n"
            "⚔️ Dominate the zones\n"
            "💎 Rule the Black Market\n"
            "This is not just a game.\n"
            "It's your *empire*. Your *legacy*.\n"
            "🎖 Ready to lead?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        player_states[user_id] = "awaiting_initial_name_action"
    else:
        # Existing player, show base UI
        logger.info(f"Existing user {user_id} ({player_data.get('commander_name', 'N/A')}) started the bot.")
        await send_base_ui(update, context, player_data)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer() # Acknowledge the callback query to remove loading animation

    user_id = query.from_user.id
    current_state = player_states.get(user_id)
    callback_data = query.data

    logger.info(f"User {user_id} current state: {current_state}, Callback Data: {callback_data}")

    if callback_data == "set_commander_name" and current_state == "awaiting_initial_name_action":
        await query.edit_message_text(
            "Please type your desired Commander Name:\n"
            "(Min 3, Max 15 characters. Alpha-numeric only. Case-sensitive.)"
        )
        player_states[user_id] = "awaiting_commander_name_input"
    elif callback_data == "enter_your_base" and current_state == "registration_complete":
        player_data = db_manager.get_player_data(user_id)
        if player_data:
            await send_base_ui(update, context, player_data)
        else:
            await query.edit_message_text("Error: Player data not found. Please try /start again.")
            player_states.pop(user_id, None) # Clear state
    # --- Placeholder for other menu callback_data ---
    elif callback_data == "build_menu":
        await query.edit_message_text("⚒️ You are in the Build Menu! (Coming soon...)")
        # In later phases, this will call a dedicated function like send_build_menu_ui()
        player_states[user_id] = "build_view"
        # Add a back button for easier navigation
        await query.message.reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back to Base", callback_data="back_to_base")]]))
    elif callback_data == "train_menu":
        await query.edit_message_text("🪖 You are in the Train Menu! (Coming soon...)")
        player_states[user_id] = "train_view"
        await query.message.reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back to Base", callback_data="back_to_base")]]))
    elif callback_data == "back_to_base":
        player_data = db_manager.get_player_data(user_id)
        if player_data:
            await send_base_ui(update, context, player_data)
        else:
            await query.edit_message_text("Error: Player data not found. Please try /start again.")
            player_states.pop(user_id, None)

    else:
        # Fallback for unhandled callbacks or incorrect state transitions
        logger.warning(f"Unhandled callback '{callback_data}' in state '{current_state}' for user {user_id}")
        await query.edit_message_text("Sorry, I don't understand that action right now. Please use the available buttons or type /start.")
        player_states.pop(user_id, None) # Clear state if something goes wrong


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