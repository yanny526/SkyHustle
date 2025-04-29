# systems/status_system.py

from telegram import Update
from telegram.ext import ContextTypes
from utils.ui_helpers import render_status_panel
from systems.tutorial_system import get_commander_name

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status — Show your commander name, resources, army, timers, and shield.
    """
    player_id = str(update.effective_user.id)
    name = get_commander_name(player_id)
    panel = render_status_panel(player_id)

    # You can prepend a header if you like
    header = f"👤 Commander: *{name}*\n"
    await update.message.reply_text(header + panel, parse_mode="Markdown")
