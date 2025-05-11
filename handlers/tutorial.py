"""
Tutorial system for SkyHustle
Manages the step-by-step tutorial for new players
"""
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants import TUTORIAL_STEPS
from modules.player import update_player
from utils.logger import get_logger

logger = get_logger(__name__)

async def start_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the tutorial sequence"""
    player_id = str(update.effective_user.id)
    query = update.callback_query
    
    # Set tutorial state in context
    context.user_data["tutorial_step"] = "welcome"
    context.user_data["tutorial_start_time"] = datetime.now()
    
    # Get first step message
    welcome_step = TUTORIAL_STEPS[0]
    
    if query:
        await query.edit_message_text(welcome_step["message"])
    else:
        await update.message.reply_text(welcome_step["message"])

async def skip_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip the tutorial sequence"""
    player_id = str(update.effective_user.id)
    query = update.callback_query
    
    # Mark tutorial as completed in player data
    await update_player(player_id, {"tutorial_completed": True})
    
    # Clear tutorial state
    if "tutorial_step" in context.user_data:
        del context.user_data["tutorial_step"]
    if "tutorial_start_time" in context.user_data:
        del context.user_data["tutorial_start_time"]
    
    if query:
        await query.edit_message_text(
            "Tutorial skipped. You can always start it again with /tutorial start.\n\n"
            "Use /status to see your base or /help to see available commands."
        )
    else:
        await update.message.reply_text(
            "Tutorial skipped. You can always start it again with /tutorial start.\n\n"
            "Use /status to see your base or /help to see available commands."
        )

async def handle_tutorial_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages during tutorial"""
    player_id = str(update.effective_user.id)
    
    # Check if user is in tutorial mode
    current_step = context.user_data.get("tutorial_step")
    if not current_step:
        # Not in tutorial mode, ignore
        return
    
    user_message = update.message.text
    
    # Find current step
    current_step_data = None
    for step in TUTORIAL_STEPS:
        if step["id"] == current_step:
            current_step_data = step
            break
    
    if not current_step_data:
        logger.error(f"Invalid tutorial step: {current_step}")
        await update.message.reply_text(
            "❌ An error occurred in the tutorial. Please use /tutorial start to restart."
        )
        return
    
    # Process message based on current step
    # For now, we'll just provide guidance to use commands instead
    await update.message.reply_text(
        f"To proceed with the tutorial, please use the commands as instructed.\n\n"
        f"Current instruction: {current_step_data['next_instruction']}"
    )

async def get_tutorial_step(player_id, context):
    """Get the current tutorial step for a player"""
    return context.user_data.get("tutorial_step")

async def set_tutorial_step(player_id, context, step):
    """Set the current tutorial step for a player"""
    context.user_data["tutorial_step"] = step
