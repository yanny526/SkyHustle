# systems/tutorial_system.py

import datetime
from telegram import Update
from telegram.ext import ContextTypes
from systems import (
    timer_system,
    army_system,
    mission_system,
    shop_system,
    building_system,
)
from utils.ui_helpers import render_status_panel

# === Tutorial State Stores ===
# player_id → current tutorial step (1–13)
tutorial_progress: dict[str, int] = {}
# player_id → chosen commander name
player_names: dict[str, str] = {}
# player_id → datetime when starter shield expires
shield_expirations: dict[str, datetime.datetime] = {}

# === Helpers ===
def get_commander_name(player_id: str) -> str:
    """Return stored commander name or default."""
    return player_names.get(player_id, "Commander")

def ensure_step(player_id: str, step: int) -> bool:
    """Check if the player is exactly at the given tutorial step."""
    return tutorial_progress.get(player_id, 0) == step

# === Part 1: Tutorial Initialization (/tutorial) ===
async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    tutorial_progress[player_id] = 1
    await update.message.reply_text(
        "🛰️ **Welcome to SkyHustle Tutorial!**\n\n"
        "Commander, what shall we call you?\n"
        "Type `/setname [Your Name]` to choose your identity."
    )

# === Part 1.1: Set Commander Name (/setname) ===
async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 1):
        return await update.message.reply_text("⚠️ Please start the tutorial first with `/tutorial`.")
    if not context.args:
        return await update.message.reply_text("⚡ Usage: `/setname [Your Name]`")

    name = " ".join(context.args).strip()
    player_names[player_id] = name
    tutorial_progress[player_id] = 2

    await update.message.reply_text(
        f"👋 Welcome, Commander **{name}**!\n"
        "🔰 Your identity is set.\n\n"
        "Type `/ready` when you’re prepared to activate your 4-day starter shield.\n\n"
        + render_status_panel(player_id)
    )

# === Part 2: Activate Starter Shield (/ready) ===
async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 2):
        return await update.message.reply_text("⚠️ You need to set your name first with `/setname [Your Name]`.")

    expiration = datetime.datetime.now() + datetime.timedelta(days=4)
    shield_expirations[player_id] = expiration
    tutorial_progress[player_id] = 3

    await update.message.reply_text(
        f"🛡️ Starter Shield is active until {expiration:%Y-%m-%d %H:%M:%S}!\n\n"
        "🏗️ **Step 1**: Build Your Command Center\n"
        "Type `/build command_center` to construct your HQ — this unlocks your Empire’s capacity.\n\n"
        + render_status_panel(player_id)
    )

# === Part 3: Build Command Center (/build) ===
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build [building] — either run the tutorial step (if step 3)
                        or hand off to the real building_system.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id, 0)

    if step == 3:
        if context.args != ["command_center"]:
            return await update.message.reply_text("⚙️ Usage: `/build command_center` to construct your HQ.")
        tutorial_progress[player_id] = 4
        return await update.message.reply_text(
            "🏗️ **Construction Complete!**\n\n"
            "Your Command Center is now operational.\n"
            "🎯 **Step 2**: Start mining resources!\n"
            "Type `/mine metal 500` to begin extracting Metal.\n\n"
            + render_status_panel(player_id)
        )

    # Delegate to your real building handlers
    return await building_system.build(update, context)

# === Part 4: Tutorial Mining (/mine) ===
async def tutorial_mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 4):
        return await timer_system.start_mining(update, context)

    if context.args != ["metal", "500"]:
        return await update.message.reply_text("⚙️ Tutorial: Type `/mine metal 500` to extract 500 Metal.")

    await timer_system.start_mining(update, context)
    tutorial_progress[player_id] = 5
    await update.message.reply_text(
        "⛏️ Excellent! Your Metal mining has begun.\n"
        "🔎 **Step 5**: Check your mining progress with `/minestatus`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 5: Check Mining Status (/minestatus) ===
async def tutorial_mine_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 5):
        return await timer_system.mining_status(update, context)

    await timer_system.mining_status(update, context)
    tutorial_progress[player_id] = 6
    await update.message.reply_text(
        "🔎 Great! You’ve checked your mining progress.\n"
        "⏳ **Step 6**: Claim your mined Metal with `/claimmine`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 6: Claim Mined Resources (/claimmine) ===
async def tutorial_claim_mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 6):
        return await timer_system.claim_mining(update, context)

    await timer_system.claim_mining(update, context)
    tutorial_progress[player_id] = 7
    await update.message.reply_text(
        "🎉 Well done — your Metal is now in your stores!\n"
        "🏭 **Step 7**: Train your first Soldiers with `/train soldier 10`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 7: Tutorial Training (/train) ===
async def tutorial_train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 7):
        return await army_system.train_units(update, context)

    if context.args != ["soldier", "10"]:
        return await update.message.reply_text("⚙️ Tutorial: Type `/train soldier 10` to enlist 10 Soldiers.")

    await army_system.train_units(update, context)
    tutorial_progress[player_id] = 8
    await update.message.reply_text(
        "🏭 Amazing! Your Soldiers are training.\n"
        "🔍 **Step 8**: Check training progress with `/trainstatus`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 8: Tutorial Training Status (/trainstatus) ===
async def tutorial_trainstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 8):
        return await army_system.training_status(update, context)

    await army_system.training_status(update, context)
    tutorial_progress[player_id] = 9
    await update.message.reply_text(
        "🔍 Nice! You’ve checked your training progress.\n"
        "🎉 **Step 9**: Claim your trained Soldiers with `/claimtrain`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 9: Tutorial Claim Training (/claimtrain) ===
async def tutorial_claim_train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 9):
        return await army_system.claim_training(update, context)

    await army_system.claim_training(update, context)
    tutorial_progress[player_id] = 10
    await update.message.reply_text(
        "🎉 Congratulations! You’ve claimed your first Soldiers.\n"
        "📜 **Step 10**: View your full army roster with `/army`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 10: Tutorial View Army (/army) ===
async def tutorial_army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 10):
        return await army_system.view_army(update, context)

    await army_system.view_army(update, context)
    tutorial_progress[player_id] = 11
    await update.message.reply_text(
        "🛡️ Excellent! You’re familiar with your forces.\n"
        "📜 **Step 11**: View your missions with `/missions`.\n\n"
        + render_status_panel(player_id)
    )

# === Part 11: Tutorial Missions (/missions) ===
async def tutorial_missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 11):
        return await mission_system.missions(update, context)

    await mission_system.missions(update, context)
    tutorial_progress[player_id] = 12
    await update.message.reply_text(
        "📜 Well done! These are your Daily Missions.\n"
        "🛒 **Step 12**: Open the shop with `/shop` to see what you can buy.\n\n"
        + render_status_panel(player_id)
    )

# === Part 12: Tutorial Shop (/shop) ===
async def tutorial_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not ensure_step(player_id, 12):
        return await shop_system.shop(update, context)

    await shop_system.shop(update, context)
    tutorial_progress[player_id] = 13
    await update.message.reply_text(
        "🛒 Great! These are the Normal Shop items.\n"
        "💡 **Step 13**: Purchase your first item with `/buy [item_id]`.\n\n"
        + render_status_panel(player_id)
    )
