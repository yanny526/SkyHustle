# handlers/attack.py

import time
import random
import json
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from modules.unit_manager import UNITS
from modules.challenge_manager import load_challenges, update_player_progress

# … your DEPLOY_SHEET / PEND_SHEET setup stays the same …

# ─────────────────────────────────────────────────────────────────────────────
# 1) The “Attack Protocols” help card
# ─────────────────────────────────────────────────────────────────────────────
async def _show_attack_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "----- 🏰 *COMMAND CENTER: Attack Protocols* -----\n\n"
        "Welcome, Commander! Issue your orders with confidence:\n\n"
        "=== ⚔️ Standard Assault ===\n"
        "`/attack EnemyCommander -u infantry:5 tanks:2`\n"
        "→ Launch a combined arms strike.\n\n"
        "=== 🔎 Recon Only ===\n"
        "`/attack EnemyCommander --scout-only -s 3`\n"
        "→ Send 3 scouts to gather intel.\n\n"
        "=== ❌ Abort Mission ===\n"
        "`/attack -c <CODE>`\n"
        "→ Cancel an en route mission.\n\n"
        "After dispatch, press *View Pending* below to track missions."
    )
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(text,
                                        parse_mode=ParseMode.MARKDOWN,
                                        reply_markup=kb)
    else:
        # callback_query path
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text,
                                                      parse_mode=ParseMode.MARKDOWN,
                                                      reply_markup=kb)

# ─────────────────────────────────────────────────────────────────────────────
# 2) Your existing scout_report_job & combat_resolution_job…
# ─────────────────────────────────────────────────────────────────────────────
async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    …  # unchanged

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    …  # unchanged

# ─────────────────────────────────────────────────────────────────────────────
# 3) Main /attack handler
# ─────────────────────────────────────────────────────────────────────────────
@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args.copy()

    # 1) If user just hit the “Attack” button (no args + callback_query),
    #    or typed `/attack` with no args, show the help card.
    if not args:
        return await _show_attack_help(update, context)

    # 2) Cancellation flag
    if "-c" in args:
        …  # your existing cancellation logic
        return

    # 3) Otherwise, normal dispatch (scout-only, -u, -s, etc.)
    …  # the rest of your existing attack code

# ─────────────────────────────────────────────────────────────────────────────
# 4) CallbackQueryHandler to re‑show the help card when 🔄 Attack is tapped
# ─────────────────────────────────────────────────────────────────────────────
async def attack_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "attack":
        return await _show_attack_help(update, context)

# ─────────────────────────────────────────────────────────────────────────────
# 5) Registering both a CommandHandler and a CallbackQueryHandler
# ─────────────────────────────────────────────────────────────────────────────
handler          = CommandHandler("attack", attack)
callback_handler = CallbackQueryHandler(attack_button, pattern="^attack$")
