from telegram import Update
from telegram.ext import ContextTypes
from utils.ui_helpers import render_status_panel

# === Tutorial State ===
# Tracks tutorial step per player
tutorial_progress = {}
# Stores chosen commander name per player
player_names = {}

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /tutorial - Start the first-time player tutorial.
    """
    player_id = str(update.effective_user.id)
    # Initialize tutorial to step 1
    tutorial_progress[player_id] = 1
    await update.message.reply_text(
        "🛰️ Welcome to SkyHustle Tutorial!\n\n"
        "Commander, what shall we call you?\n"
        "Type /setname [Your Name] to choose your identity."
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname [name] - Let player choose their commander name and advance tutorial.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    # Ensure tutorial started and at step 1
    if step != 1:
        await update.message.reply_text(
            "⚠️ You need to start the tutorial first by typing /tutorial."
        )
        return
    # Validate name args
    if not context.args:
        await update.message.reply_text(
            "⚡ Usage: /setname [Your Name]"
        )
        return
    # Save name and advance
    name = " ".join(context.args)
    player_names[player_id] = name
    tutorial_progress[player_id] = 2
    # Greet and prompt next step
    await update.message.reply_text(
        f"👋 Welcome Commander {name}!\n"
        "🔰 Your identity is set.\n\n"
        "Type /ready when you're prepared to activate your 4-day starter shield."
    )

async def get_name(player_id: str) -> str:
    """
    Helper to retrieve stored commander name or default.
    """
    return player_names.get(player_id, "Commander")

