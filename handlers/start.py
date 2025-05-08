# handlers/start.py

from telegram import Update
from telegram.ext import ContextTypes
import time

from bot.modules.player import Player
from utils.format import section_header

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name

    # Check if player exists
    players = get_rows("Players")
    player_exists = any(row[0] == uid for row in players[1:])

    if not player_exists:
        # Register new player
        new_player = Player(uid, name)
        append_row("Players", list(new_player.to_dict().values()))
        await update.message.reply_text(
            f"🚀 Welcome to SkyHustle, Commander {name}! 🚀\n\n"
            "You've been registered with:\n"
            "1000💰 Credits | 500⛏️ Minerals | 200⚡ Energy\n"
            "Use these commands to get started:\n"
            "/status - View your base status\n"
            "/build - Construct buildings\n"
            "/train - Train units\n"
            "/attack - Attack other players\n"
            "/shop - Visit the normal shop\n"
            "/blackmarket - Visit the black market",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"Welcome back, Commander {name}! Use /status to view your base.",
            parse_mode="Markdown"
        )