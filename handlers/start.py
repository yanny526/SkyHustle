# handlers/start.py

from telegram import Update
from telegram.ext import ContextTypes
import time

from modules.player import Player
from utils.format import section_header
from sheets_service import get_rows, append_row    # <— ensure both are imported

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name

    # Fetch all players
    players = get_rows("Players")
    player_exists = any(row[0] == uid for row in players[1:])

    if not player_exists:
        # New player: give starting resources
        append_row("Players", [uid, name, 1000, 500, 200])
        await update.message.reply_text(
            section_header("WELCOME", "👋", "blue") + "\n\n"
            "Welcome! You’ve received:\n"
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
