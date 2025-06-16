"""
Base handler class for SkyHustle.
Provides common functionality for all command handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Any 

"""
Base Handler: player registration.
"""
import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from utils.sheets_helper import create_player, load_player

# Conversation state
ASK_NAME = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    existing = await load_player(str(user.id))
    if existing:
        await update.message.reply_text(
            f"👋 You're already registered as *{existing['name']}*!",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 Welcome to SkyHustle!\nPlease choose your **in-game name**:",
        parse_mode="Markdown",
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    user_id = str(update.effective_user.id)
    try:
        await create_player(user_id, name)
        await update.message.reply_text(
            f"✅ Registered successfully as *{name}*! Use /base to view your base.",
            parse_mode="Markdown",
        )
    except Exception:
        logging.exception("Failed to register player")
        await update.message.reply_text(
            "❌ Registration failed. Please try again later."
        )
    return ConversationHandler.END

def registration_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
        fallbacks=[],
    ) 