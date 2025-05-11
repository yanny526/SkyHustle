"""
Base command handlers for the SkyHustle Telegram bot.
These handlers manage core game functionality and basic commands.
"""
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes
from modules.player import get_player, create_player, update_player, claim_daily_reward
from utils.formatter import format_status_message, format_error, format_success, format_info
from utils.validators import validate_name

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command - introduces the game and starts tutorial."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        # New player, create their profile
        player = create_player(user.id, user.first_name)
        
        welcome_text = (
            f"Welcome to *SkyHustle*, {user.first_name}! 🚀\n\n"
            "Build your aerial base, train units, research technologies, and "
            "battle for supremacy in the skies!\n\n"
            "Would you like to start the tutorial?"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Begin Tutorial", callback_data=json.dumps({"cmd": "tutorial", "action": "start"})),
                InlineKeyboardButton("Skip Tutorial", callback_data=json.dumps({"cmd": "tutorial", "action": "skip"}))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        # Returning player
        welcome_back_text = (
            f"Welcome back, *{player['display_name']}*! 🚀\n\n"
            "Your aerial base awaits your command\\.\n"
            "Use /status to see your current resources and progress\\."
        )
        
        await update.message.reply_text(
            welcome_back_text,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command - shows player resources and status."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        await update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    status_message = format_status_message(player)
    await update.message.reply_text(
        status_message,
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command - shows available commands."""
    help_text = (
        "*SkyHustle Commands:*\n\n"
        "🔹 */start* \\- Begin your journey\n"
        "🔹 */status* \\- View your resources and base\n"
        "🔹 */build <structure> \\[quantity\\]* \\- Construct buildings\n"
        "🔹 */train <unit> \\[count\\]* \\- Train military units\n"
        "🔹 */research \\[tech_id\\]* \\- Research technologies\n"
        "🔹 */alliance <subcmd>* \\- Manage your alliance\n"
        "🔹 */attack <player_id>* \\- Attack another player\n"
        "🔹 */scan* \\- Find potential targets\n"
        "🔹 */daily* \\- Claim daily reward\n"
        "🔹 */setname <name>* \\- Change your display name\n"
        "🔹 */tutorial* \\- Restart the tutorial\n"
        "\nFor detailed help on any command, use: */help <command>*"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /setname command - allows player to set their display name."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        await update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    # Check if a name was provided
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            format_error("Please provide a name. Example: /setname Commander Smith")
        )
        return
    
    # Join all arguments as the name
    new_name = " ".join(context.args)
    
    # Validate the name
    validation_result = validate_name(new_name)
    if validation_result != "valid":
        await update.message.reply_text(
            format_error(f"Invalid name: {validation_result}")
        )
        return
    
    # Update the player's name
    success = update_player(user.id, {"display_name": new_name})
    
    if success:
        await update.message.reply_text(
            format_success(f"Your display name has been updated to {new_name}!")
        )
    else:
        await update.message.reply_text(
            format_error("Failed to update your name. Please try again later.")
        )

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /daily command - claims daily rewards."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        await update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    result = claim_daily_reward(user.id)
    
    if result['success']:
        rewards = result['rewards']
        streak = result.get('streak', 1)
        
        reward_text = (
            f"*Daily Reward Claimed\\!* 🎁\n\n"
            f"You received:\n"
            f"💰 *{rewards['credits']}* credits\n"
            f"🔷 *{rewards['minerals']}* minerals\n"
            f"⚡ *{rewards['energy']}* energy\n\n"
            f"Current streak: *{streak}* days"
        )
        
        await update.message.reply_text(
            reward_text,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            format_error(result['message'])
        )

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /weather command - provides fun ambient weather messages."""
    import random
    
    weather_messages = [
        "Clear skies above your aerial base today. Perfect for reconnaissance missions! ☀️",
        "A storm is brewing on the horizon. Defensive systems at 120% capacity recommended. ⛈️",
        "Light cloud cover provides ideal conditions for stealth operations. 🌤️",
        "Solar flare activity detected! Energy production boosted by 5% for the next hour. ☀️⚡",
        "Fog has settled around the lower levels of your base. Watch for surprise attacks! 🌫️",
        "High winds in your sector. Aerial unit movement speed reduced by 10%. 💨",
        "Meteor shower expected tonight. Research teams are excited about potential mineral deposits! 🌠",
        "Aurora borealis visible from your command center. Crew morale has increased! 🌌",
        "Perfect atmospheric conditions for testing that new prototype aircraft! 🛩️",
        "Strange atmospheric phenomenon detected. Possible alien technology signatures? 👽"
    ]
    
    chosen_message = random.choice(weather_messages)
    await update.message.reply_text(format_info(chosen_message))

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /events command - shows active events."""
    # In a full implementation, this would fetch actual events from the database
    await update.message.reply_text(
        format_info("No active events at this time. Check back later!")
    )

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /achievements command - shows player achievements."""
    # In a full implementation, this would fetch actual achievements from the database
    await update.message.reply_text(
        format_info("Achievement system coming soon! Stay tuned.")
    )

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /save command - force saves game state to Google Sheets."""
    user = update.effective_user
    # In a full implementation, this would trigger an immediate save to Google Sheets
    await update.message.reply_text(
        format_success("Game state saved successfully.")
    )

async def load(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /load command - force loads game state from Google Sheets."""
    user = update.effective_user
    # In a full implementation, this would trigger an immediate load from Google Sheets
    await update.message.reply_text(
        format_success("Game state loaded successfully.")
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /leaderboard command - shows rankings."""
    scope = "global"
    if context.args and len(context.args) > 0:
        scope = context.args[0].lower()
    
    # In a full implementation, this would fetch actual leaderboard data
    await update.message.reply_text(
        format_info(f"{scope.capitalize()} leaderboard coming soon!")
    )

async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /notifications command - manages notification settings."""
    # In a full implementation, this would allow configuring notification preferences
    await update.message.reply_text(
        format_info("Notification settings coming soon!")
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = json.loads(query.data)
        command = data.get("cmd")
        
        if command == "tutorial":
            action = data.get("action")
            if action == "start":
                from handlers.tutorial_handlers import start_tutorial
                await start_tutorial(update, context)
            elif action == "skip":
                await query.edit_message_text(
                    "Tutorial skipped! Use /status to check your base and /help to see available commands."
                )
        elif command == "build":
            building_id = data.get("id")
            from handlers.building_handlers import handle_build_callback
            await handle_build_callback(update, context, building_id)
        # Add more callback handlers as needed
            
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await query.edit_message_text(f"An error occurred: {str(e)}")
