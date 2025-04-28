# systems/tutorial_system.py

import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.ui_helpers import render_status_panel

# State stores
tutorial_progress = {}  # player_id → step
player_names      = {}  # player_id → chosen name

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /tutorial — start the first-time player tutorial.
    """
    player_id = str(update.effective_user.id)
    tutorial_progress[player_id] = 1
    await update.message.reply_text(
        "🛰️ **Welcome to SkyHustle Tutorial!**\n\n"
        "Commander, what shall we call you?\n"
        "Type `/setname [Your Name]` to choose your identity."
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname [name] — let player choose their commander name.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)
    if step != 1:
        return await update.message.reply_text(
            "⚠️ You need to start the tutorial first with `/tutorial`."
        )
    if not context.args:
        return await update.message.reply_text("⚡ Usage: `/setname [Your Name]`")

    # Save name and advance
    name = " ".join(context.args)
    player_names[player_id] = name
    tutorial_progress[player_id] = 2

    panel = render_status_panel(player_id)
    await update.message.reply_text(
        f"👋 Welcome, Commander **{name}**!\n"
        "🔰 Your identity is set.\n\n"
        "Type `/ready` when you’re prepared to activate your 4-day starter shield."
        f"\n\n{panel}"
    )

def get_commander_name(player_id: str) -> str:
    """
    Helper to retrieve stored commander name or default.
    """
    return player_names.get(player_id, "Commander")
# === Part 2: Activate Starter Shield (/ready) ===

# Track shield expirations per player
shield_expirations = {}  # player_id → datetime

async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /ready — activate your 4-day starter shield and prompt your first build.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)

    if step != 2:
        return await update.message.reply_text(
            "⚠️ You need to set your name first with `/setname [Your Name]`."
        )

    # Activate 4-day shield
    expiration = datetime.datetime.now() + datetime.timedelta(days=4)
    shield_expirations[player_id] = expiration
    tutorial_progress[player_id] = 3

    panel = render_status_panel(player_id)
    await update.message.reply_text(
        f"🛡️ Starter Shield is now ACTIVE until {expiration.strftime('%Y-%m-%d %H:%M:%S')}!\n\n"
        "🏗️ Step 1: Build Your Command Center\n"
        "Type `/build command_center` to construct your HQ—this unlocks your Empire’s capacity.\n\n"
        f"{panel}"
    )


