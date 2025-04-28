# tutorial_system.py

from telegram import Update
from telegram.ext import ContextTypes
from utils.ui_helpers import render_status_panel

# === Tutorial State ===
# Tracks tutorial step per player
# 1: set name, 2: ready shield, 3: build CC, 4: mine, 5: claim mine, 6: train, 7: claim train, 8: attack
tutorial_progress = {}
# Stores chosen commander name per player
player_names = {}

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /tutorial - Start the first-time player tutorial.
    """
    pid = str(update.effective_user.id)
    tutorial_progress[pid] = 1
    await update.message.reply_text(
        "🛰️ Welcome to SkyHustle Tutorial!\n\n"
        "Commander, what shall we call you?\n"
        "Type /setname [Your Name] to choose your identity."
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname [name] - Let player choose their commander name and advance tutorial.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 1:
        await update.message.reply_text("⚠️ Please start with /tutorial.")
        return
    if not context.args:
        await update.message.reply_text("⚡ Usage: /setname [Your Name]")
        return
    name = " ".join(context.args)
    player_names[pid] = name
    tutorial_progress[pid] = 2
    await update.message.reply_text(
        f"👋 Welcome Commander {name}!\n"
        "🔰 Your identity is set.\n\n"
        "Type /ready when you're prepared to activate your 4-day starter shield."
    )

# --- Part 2: Activate Starter Shield ---
async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /ready - Activate shield and continue tutorial.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 2:
        await update.message.reply_text("⚠️ You need to set your name first with /setname.")
        return
    tutorial_progress[pid] = 3
    name = player_names.get(pid, "Commander")
    await update.message.reply_text(
        f"🛡️ Starter Shield activated! Welcome, {name}."
        " You are safe for 4 days.\n\n"
        "Let’s build your Command Center.\n"
        "Type /build command_center to begin construction."
    )

# --- Part 3: Build Command Center ---
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build [building] - Simulate building and advance tutorial.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 3:
        await update.message.reply_text("⚠️ That’s not on our agenda right now.")
        return
    if not context.args or context.args[0].lower() != 'command_center':
        await update.message.reply_text("⚒️ To continue, type /build command_center.")
        return
    tutorial_progress[pid] = 4
    await update.message.reply_text(
        "🏗️ Command Center constructed!\n"
        "Great work. Now let's mine some resources."
        "\nType /mine metal 100 to start mining."
    )

# --- Part 4: Tutorial Mining ---
async def tutorial_mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Intercepts /mine during tutorial.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 4:
        return  # let normal handler take over
    # Expect exactly: /mine metal 100
    if len(context.args)==2 and context.args[0].lower()=='metal' and context.args[1]=='100':
        tutorial_progress[pid] = 5
        await update.message.reply_text(
            "⛏️ Mining 100 Metal started!\n"
            "...fast-forwarding time for tutorial...\n"
            "🏁 Mining complete! Type /claimmine to claim your metal."
        )
    else:
        await update.message.reply_text("⚡ Tutorial expects /mine metal 100. Try that!\n\n"+render_status_panel(pid))

# --- Part 5: Claim Mining ---
async def tutorial_claimmine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /claimmine during tutorial flow.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 5:
        return
    tutorial_progress[pid] = 6
    # Grant tutorial resource (in-memory)
    # Normally we'd update Google Sheets here
    await update.message.reply_text(
        "🎉 You claimed 100 Metal!\n"
        "Resources are key. Now let's train your first troops.\n"
        "Type /train soldier 10 to begin training."
    )

# --- Part 6: Tutorial Training ---
async def tutorial_train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train during tutorial flow.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 6:
        return
    if len(context.args)==2 and context.args[0].lower()=='soldier' and context.args[1]=='10':
        tutorial_progress[pid] = 7
        await update.message.reply_text(
            "🏭 Training 10 Soldiers started...\n"
            "✅ Training complete! Type /claimtrain to add them to your army."
        )
    else:
        await update.message.reply_text("⚡ Tutorial expects /train soldier 10. Give it another try.\n\n"+render_status_panel(pid))

# --- Part 7: Claim Training ---
async def tutorial_claimtrain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /claimtrain during tutorial.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 7:
        return
    tutorial_progress[pid] = 8
    await update.message.reply_text(
        "🎉 You now have 10 Soldiers in your army!\n"
        "Great progress, Commander. Your next challenge: combat.\n"
        "Type /attack TRAINER to battle the practice dummy."
    )

# --- Part 8: Tutorial Attack & Completion ---
async def tutorial_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack during tutorial.
    """
    pid = str(update.effective_user.id)
    if tutorial_progress.get(pid) != 8:
        return
    if len(context.args)==1 and context.args[0].upper()=='TRAINER':
        tutorial_progress[pid] = 9
        await update.message.reply_text(
            "⚔️ You attacked the practice dummy and emerged victorious!\n"
            "🏆 Tutorial complete! Welcome to the true skies of SkyHustle.\n"
            "Type /help to explore all commands, or /status at any time to view your empire.\n"
            + render_status_panel(pid)
        )
    else:
        await update.message.reply_text("⚡ Tutorial expects `/attack TRAINER`. Try again!\n\n"+render_status_panel(pid))

# Helper to get name
async def get_name(player_id: str) -> str:
    return player_names.get(player_id, "Commander")
