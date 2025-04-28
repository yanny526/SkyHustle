from telegram import Update
from telegram.ext import ContextTypes
from utils.ui_helpers import render_status_panel

# === Tutorial State ===
# Tracks tutorial step per player
# 1=setname, 2=ready, 3=build, 4=mine, 5=claimmine, 6=train, 7=army, 8=complete
 tutorial_progress = {}
# Stores chosen commander name per player
player_names = {}
# Track shield status (True if active)
player_shields = {}

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    tutorial_progress[player_id] = 1
    player_shields[player_id] = False
    await update.message.reply_text(
        "🛰️ Welcome to SkyHustle Tutorial!\n\n"
        "Commander, what shall we call you?\n"
        "Type /setname [Your Name] to choose your identity.\n\n"
        + render_status_panel(player_id)
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 1:
        await update.message.reply_text("⚠️ Please start the tutorial with /tutorial.")
        return
    if not context.args:
        await update.message.reply_text("⚡ Usage: /setname [Your Name]")
        return
    name = " ".join(context.args)
    player_names[player_id] = name
    tutorial_progress[player_id] = 2
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        f"👋 Welcome Commander {name}!\n"
        "🔰 Next: activate your 4-day starter shield.\n"
        "Type /ready when you're prepared.\n\n"
        + panel
    )

async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 2:
        await update.message.reply_text("⚠️ Use /setname first.")
        return
    player_shields[player_id] = True
    tutorial_progress[player_id] = 3
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🛡️ Shield activated! You are safe for 4 days.\n"
        "🛠️ Step 1: Build your Command Center.\n"
        "Type /build command_center\n\n"
        + panel
    )

async def deactivate_shield(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if not player_shields.get(player_id):
        await update.message.reply_text("🔓 Shield is not active.")
        return
    player_shields[player_id] = False
    await update.message.reply_text(
        "🔓 Starter shield deactivated. Enemies can now attack!"
    )

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 3:
        return  # let building_system handle elsewhere
    args = context.args
    if len(args)!=1 or args[0].lower()!='command_center':
        await update.message.reply_text(
            "⚙️ Usage: /build command_center"
        )
        return
    tutorial_progress[player_id] = 4
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🏗️ Command Center constructed! Level 1 unlocked.\n"
        "⛏️ Step 2: Start mining resources.\n"
        "Type /mine metal 500\n\n"
        + panel
    )

# Part 5: Mining step
async def tutorial_mine(update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 4:
        return
    # let timer_system.start_mining run normally, then advance
    tutorial_progress[player_id] = 5
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "⛏️ Good start! Now claim your resources.\n"
        "Type /claimmine to collect your mining haul.\n\n"
        + panel
    )

# Part 6: Claim mining
async def tutorial_claim(update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 5:
        return
    tutorial_progress[player_id] = 6
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🎉 Resources claimed!\n"
        "🏭 Step 3: Train your first troops.\n"
        "Type /train soldier 10\n\n"
        + panel
    )

# Part 7: Training
async def tutorial_train(update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 6:
        return
    tutorial_progress[player_id] = 7
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🛡️ Training underway!\n"
        "👀 Step 4: View your army.\n"
        "Type /army to inspect your forces.\n\n"
        + panel
    )

# Part 8: View army & complete
async def tutorial_army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 7:
        return
    tutorial_progress[player_id] = 8
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🏁 Congratulations! You have completed the SkyHustle tutorial.\n"
        "Use /status anytime to check your empire. Happy conquering, Commander!\n\n"
        + panel
    )
