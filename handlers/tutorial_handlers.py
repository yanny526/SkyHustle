"""
Tutorial related command handlers for the SkyHustle Telegram bot.
These handlers manage the tutorial flow for new players.
"""
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from modules.player import get_player, update_player
from utils.formatter import format_error, format_success, format_info

logger = logging.getLogger(__name__)

# Tutorial steps
TUTORIAL_STEPS = [
    {
        "id": "welcome",
        "message": (
            "Welcome to the SkyHustle tutorial!\n\n"
            "I'll guide you through the basics of building your aerial base "
            "and commanding your forces."
        ),
        "next_step": "status_command"
    },
    {
        "id": "status_command",
        "message": (
            "Let's start by checking your base status.\n\n"
            "Type /status to see your current resources and buildings."
        ),
        "expected_command": "/status",
        "next_step": "build_command"
    },
    {
        "id": "build_command",
        "message": (
            "Great! Now let's construct your first building.\n\n"
            "Type /build solar_array to build a Solar Array that generates energy."
        ),
        "expected_command": "/build solar_array",
        "next_step": "train_command"
    },
    {
        "id": "train_command",
        "message": (
            "Excellent! You now have a structure generating energy.\n\n"
            "Let's train some units to defend your base.\n"
            "Type /train drone to train a basic reconnaissance drone."
        ),
        "expected_command": "/train drone",
        "next_step": "setname_command"
    },
    {
        "id": "setname_command",
        "message": (
            "Your base is starting to take shape!\n\n"
            "Finally, let's personalize your commander name.\n"
            "Type /setname followed by your preferred name. For example: /setname Sky Commander"
        ),
        "expected_command": "/setname",
        "next_step": "completion"
    },
    {
        "id": "completion",
        "message": (
            "Congratulations! You've completed the basic tutorial.\n\n"
            "You now know how to:\n"
            "• Check your base status\n"
            "• Construct buildings\n"
            "• Train units\n"
            "• Customize your commander name\n\n"
            "As a reward, you've received bonus resources!\n\n"
            "What would you like to do next?"
        ),
        "next_step": None
    }
]

def tutorial(update: Update, context: CallbackContext):
    """Handler for /tutorial command - starts or skips the tutorial."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        # Create player if they don't exist
        from modules.player import create_player
        player = create_player(user.id, user.first_name)
    
    # Check for arguments
    if context.args and len(context.args) > 0:
        action = context.args[0].lower()
        
        if action == "start":
            start_tutorial(update, context)
            return
        elif action == "skip":
            # Mark tutorial as completed
            update_player(user.id, {"tutorial_completed": True})
            update.message.reply_text(
                format_success("Tutorial skipped! Use /status to check your base and /help to see available commands.")
            )
            return
    
    # If no arguments or invalid arguments, show tutorial options
    keyboard = [
        [
            InlineKeyboardButton("Begin Tutorial", callback_data=json.dumps({"cmd": "tutorial", "action": "start"})),
            InlineKeyboardButton("Skip Tutorial", callback_data=json.dumps({"cmd": "tutorial", "action": "skip"}))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Would you like to start the tutorial?",
        reply_markup=reply_markup
    )

def start_tutorial(update: Update, context: CallbackContext):
    """Starts the tutorial sequence."""
    if update.callback_query:
        # If called from a callback query
        query = update.callback_query
        user_id = query.from_user.id
        query.edit_message_text(TUTORIAL_STEPS[0]["message"])
    else:
        # If called directly from a command
        user = update.effective_user
        user_id = user.id
        update.message.reply_text(TUTORIAL_STEPS[0]["message"])
    
    # Set the player's tutorial state to the first step
    update_player(user_id, {"tutorial_step": "welcome"})

def process_tutorial_step(update: Update, context: CallbackContext):
    """Processes a tutorial step based on player input."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player or "tutorial_step" not in player:
        return False  # Not in tutorial mode
    
    current_step_id = player["tutorial_step"]
    current_step = next((step for step in TUTORIAL_STEPS if step["id"] == current_step_id), None)
    
    if not current_step:
        return False  # Invalid tutorial step
    
    # Check if this is a command expected by the current step
    if "expected_command" in current_step:
        command = update.message.text.split()[0]
        if not command.startswith(current_step["expected_command"]):
            return False  # Not the expected command
    
    # Find the next step
    next_step_id = current_step.get("next_step")
    if not next_step_id:
        # Tutorial completed
        update_player(user.id, {
            "tutorial_completed": True,
            "tutorial_step": None,
            # Award bonus resources
            "credits": player.get("credits", 0) + 500,
            "minerals": player.get("minerals", 0) + 200,
            "energy": player.get("energy", 0) + 200
        })
        
        # Show completion message with options
        keyboard = [
            [
                InlineKeyboardButton("Check Status", callback_data=json.dumps({"cmd": "status"})),
                InlineKeyboardButton("Build More", callback_data=json.dumps({"cmd": "build"}))
            ],
            [
                InlineKeyboardButton("See Help", callback_data=json.dumps({"cmd": "help"}))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            TUTORIAL_STEPS[-1]["message"],
            reply_markup=reply_markup
        )
    else:
        # Move to next tutorial step
        next_step = next((step for step in TUTORIAL_STEPS if step["id"] == next_step_id), None)
        if next_step:
            update_player(user.id, {"tutorial_step": next_step_id})
            update.message.reply_text(next_step["message"])
    
    return True  # Tutorial step processed
