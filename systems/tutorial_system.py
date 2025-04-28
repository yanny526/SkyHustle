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
# === Part 5: Check Mining Status (/minestatus) ===
async def tutorial_mine_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /minestatus — Tutorial-guided status check in step 5.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)

    # If not in tutorial step 5, delegate to normal handler
    if step != 5:
        return await timer_system.mining_status(update, context)

    # Show the normal mining status
    await timer_system.mining_status(update, context)

    # Advance tutorial to step 6
    tutorial_progress[player_id] = 6

    # Prompt next action
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🔎 Great! You’ve checked your mining progress.\n"
        "⏳ Step 6: Claim your mined Metal with `/claimmine`.\n\n"
        f"{panel}"
    )
# === Part 6: Claim Mined Resources (/claimmine) ===
async def tutorial_claim_mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /claimmine — Tutorial-guided claim in step 6.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)

    # If not in tutorial step 6, delegate to normal handler
    if step != 6:
        return await timer_system.claim_mining(update, context)

    # Execute the normal claim logic
    await timer_system.claim_mining(update, context)

    # Advance tutorial to step 7
    tutorial_progress[player_id] = 7

    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🎉 Well done—your Metal is now in your stores!\n"
        "🏭 Step 7: Train your first Soldiers with `/train soldier 10`.\n\n"
        f"{panel}"
    )
# === Part 7: Tutorial Training (/train) ===
from systems import army_system  # add this at top if not already present

async def tutorial_train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train — Tutorial-guided training in step 7.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)

    # If not in tutorial step 7, delegate to normal handler
    if step != 7:
        return await army_system.train_units(update, context)

    # Expect exactly `/train soldier 10`
    args = context.args
    if len(args) != 2 or args[0].lower() != "soldier" or args[1] != "10":
        return await update.message.reply_text(
            "⚙️ Tutorial: Type `/train soldier 10` to enlist 10 Soldiers."
        )

    # Execute the normal training logic
    await army_system.train_units(update, context)

    # Advance tutorial to step 8
    tutorial_progress[player_id] = 8

    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🏭 Amazing! Your Soldiers are training.\n"
        "🔍 Step 8: Check training progress with `/trainstatus`.\n\n"
        f"{panel}"
    )

