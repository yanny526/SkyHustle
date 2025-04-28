from telegram import Update
from telegram.ext import ContextTypes
from utils.ui_helpers import render_status_panel
from utils.google_sheets import save_building, load_resources, save_resources  # if needed

# === Tutorial State ===
# Tracks tutorial step per player
# 1: asked name, 2: name set, waiting for /ready, 3: shield active, waiting /build, 4: built CC, waiting /mine, etc.
tutorial_progress = {}
# Stores chosen commander name per player
player_names = {}

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /tutorial - Start the first-time player tutorial.
    """
    player_id = str(update.effective_user.id)
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
    if step != 1:
        await update.message.reply_text("⚠️ Start with /tutorial to begin the tutorial.")
        return

    if not context.args:
        await update.message.reply_text("⚡ Usage: /setname [Your Name]")
        return

    name = " ".join(context.args)
    player_names[player_id] = name
    tutorial_progress[player_id] = 2
    await update.message.reply_text(
        f"👋 Welcome Commander {name}!\n"
        "🔰 Your identity is set.\n\n"
        "Type /ready when you're prepared to activate your 4-day starter shield."
    )

async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /ready - Activate starter shield and prompt first build.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 2:
        await update.message.reply_text("⚠️ You need to set your name first with /setname.")
        return

    tutorial_progress[player_id] = 3
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "🛡️ Starter Shield Active (4 days)! While shielded, you cannot attack.\n\n"
        "🏗️ Step 1: Build your Command Center.\n"
        "Type /build command_center to begin construction.\n\n"
        + panel
    )

async def deactivate_shield(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /deactivate_shield - Opt out of starter shield early.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    if step != 2:
        await update.message.reply_text("⚠️ You can only deactivate shield after /setname.")
        return

    tutorial_progress[player_id] = 3
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        "⚔️ Starter Shield Deactivated. Beware of enemy attacks now!\n\n"
        "🏗️ Step 1: Build your Command Center.\n"
        "Type /build command_center to begin construction.\n\n"
        + panel
    )

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build [building] - Tutorial hook for constructing the Command Center.
    """
    player_id = str(update.effective_user.id)
    step = tutorial_progress.get(player_id)
    args = context.args
    panel = render_status_panel(player_id)

    # Ensure in the correct tutorial step and correct building
    if step != 3 or not args or args[0].lower() != 'command_center':
        await update.message.reply_text(
            "⚠️ Use /build command_center to build your Command Center during the tutorial.\n\n" + panel
        )
        return

    # Simulate building: save level=1
    try:
        save_building(player_id, 'command_center', 1)
    except Exception:
        pass  # if not implemented, ignore

    tutorial_progress[player_id] = 4
    await update.message.reply_text(
        "🏗️ Command Center Level 1 Constructed!\n"
        "Great! Now let's gather resources to power your base.\n\n"
        "⛏️ Step 2: Mine 100 Metal.\n"
        "Type /mine metal 100 to start mining.\n\n"
        + panel
    )
