# handlers/attack.py
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from sheets_service import get_rows, append_row
from utils.format_utils import section_header
from modules.combat_manager import CombatManager

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    uid = str(update.effective_user.id)
    
    if not args:
        await update.message.reply_text(
            "Usage: `/attack <player_id>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    target_id = args[0]
    players = get_rows("Players")
    
    # Find attacker's data
    attacker_name = "Unknown Commander"
    for row in players[1:]:
        if row[0] == uid:
            attacker_name = row[1]
            break
    
    # Find defender's data
    defender_name = "Unknown Commander"
    defender_found = False
    for row in players[1:]:
        if row[0] == target_id:
            defender_name = row[1]
            defender_found = True
            break
    
    if not defender_found:
        await update.message.reply_text(
            "Defender not found! Make sure you entered the correct player ID.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Initialize combat manager and resolve combat
    combat = CombatManager(uid, target_id, attacker_name, defender_name)
    report, outcome, spoils = combat.resolve_combat()

    # Send battle report to attacker
    await update.message.reply_text(
        report,
        parse_mode=ParseMode.MARKDOWN
    )

    # If it's a victory, also send report to defender
    if outcome == "victory":
        for row in players[1:]:
            if row[0] == target_id:
                try:
                    await context.bot.send_message(
                        chat_id=int(target_id),
                        text=f"You were attacked by {attacker_name}!\n\n{report}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass  # Ignore if unable to notify defender
                break

handler = CommandHandler("attack", attack)
