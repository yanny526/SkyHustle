# systems/tutorial_system.py

import datetime
from telegram import Update
from telegram.ext import ContextTypes
from systems import timer_system
from utils.ui_helpers import render_status_panel

# === Tutorial State Stores ===
# Tracks the current tutorial step for each player
# Stores chosen commander names per player
# Tracks starter shield expiration per player

tutorial_progress = {}          # player_id → step
player_names = {}               # player_id → chosen name
shield_expirations = {}         # player_id → shield expiration datetime

# === Part 1: Tutorial Initialization (/tutorial) ===
async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /tutorial — Start the first-time player tutorial.
    """
    player_id = str(update.effective_user.id)
    tutorial_progress[player_id] = 1
    await update.message.reply_text(
        "🛰️ **Welcome to SkyHustle Tutorial!**\n\n"
        "Commander, what shall we call you?\n"
        "Type `/setname [Your Name]` to choose your identity."
    )

# === Part 1.1: Set Commander Name (/setname) ===
async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname [name] — Let player choose their commander name.
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

# === Helper: Get Commander Name ===
def get_commander_name(player_id: str) -> str:
    """
    Retrieve stored commander name or default.
    """
    return player_names.get(player_id, "Commander")

# === Part 2: Activate Starter Shield (/ready) ===
async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /ready — Activate your 4-day starter shield and prompt your first build.
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
        f"🛡️ Starter Shield is active until {expiration.strftime('%Y-%m-%d %H:%M:%S')}!\n\n"
        "🏗️ Step 1: Build Your Command Center\n"
        "Type `/build command_center` to construct your HQ—this unlocks your Empire’s capacity.\n\n"
        f"{panel}"
    )

# === Part 3: Build Command Center (/build) ===
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build [building] — Construct your first tutorial building.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)
    if step != 3:
        return await update.message.reply_text(
            "⚠️ You need to activate your shield first with `/ready`."
        )

    args = context.args
    if len(args) != 1 or args[0].lower() != "command_center":
        return await update.message.reply_text(
            "⚙️ Usage: `/build command_center` to construct your HQ."
        )

    # Advance tutorial
    tutorial_progress[player_id] = 4

    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🏗️ **Construction Complete!**\n\n"
        "Your Command Center is now operational.\n"
        "🎯 Step 2: Start mining resources!\n"
        "Type `/mine metal 500` to begin extracting Metal.\n\n"
        f"{panel}"
    )

# === Part 4: Tutorial Mining (/mine) ===
async def tutorial_mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /mine — Tutorial-guided mining in step 4.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)

    # If not in tutorial step 4, delegate to normal handler
    if step != 4:
        return await timer_system.start_mining(update, context)

    # Expect exactly `/mine metal 500`
    args = context.args
    if len(args) != 2 or args[0].lower() != "metal" or args[1] != "500":
        return await update.message.reply_text(
            "⚙️ Tutorial: Type `/mine metal 500` to extract 500 Metal."
        )

    # Execute the normal mining logic
    await timer_system.start_mining(update, context)

    # Advance tutorial to step 5
    tutorial_progress[player_id] = 5

    # Prompt next action
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "⛏️ Excellent! Your Metal mining has begun.\n"
        "🔎 Step 5: Check your mining progress with `/minestatus`.\n\n"
        f"{panel}"
    )
