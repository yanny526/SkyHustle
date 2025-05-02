# handlers/attack.py

import time
import random
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <CommanderName> – attack another commander by name (tick & upgrades via decorator).
    Costs 5⚡ energy.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <CommanderName>`",
            parse_mode=ParseMode.MARKDOWN
        )
    target = args[0]

    # Load players
    players = get_rows('Players')
    attacker = defender = None
    atk_i = def_i = None
    for i, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            attacker, atk_i = row.copy(), i
        if row[1].lower() == target.lower():
            defender, def_i = row.copy(), i

    if not attacker:
        return await update.message.reply_text(
            "❗ Run /start first.", parse_mode=ParseMode.MARKDOWN
        )
    if not defender:
        return await update.message.reply_text(
            f"❌ Commander *{target}* not found.",
            parse_mode=ParseMode.MARKDOWN
        )
    if defender[0] == uid:
        return await update.message.reply_text(
            "❌ You cannot attack yourself!",
            parse_mode=ParseMode.MARKDOWN
        )

    # Deduct energy
    energy = int(attacker[5])
    if energy < 5:
        return await update.message.reply_text("❌ Not enough energy. Need 5⚡.")
    attacker[5] = str(energy - 5)
    update_row('Players', atk_i, attacker)

    # Gather credits
    aC, dC = int(attacker[3]), int(defender[3])

    # Compute army power
    def power(urow):
        total = 0
        for r in get_rows('Army')[1:]:
            if r[0] != urow[0]:
                continue
            total += int(r[2]) * {'infantry': 10, 'tanks': 50, 'artillery': 100}[r[1]]
        return total

    atk_roll = power(attacker) * random.uniform(0.9, 1.1)
    def_roll = power(defender) * random.uniform(0.9, 1.1)

    timestamp = str(int(time.time()))
    if atk_roll > def_roll:
        result = 'win'
        spoils = max(1, dC // 10)
        aC += spoils
        dC -= spoils
        msg = f"🏆 *{attacker[1]}* defeated *{defender[1]}*! Stole {spoils}💳."
    else:
        result = 'loss'
        spoils = max(1, aC // 20)
        aC -= spoils
        dC += spoils
        msg = f"💥 *{attacker[1]}* was defeated by *{defender[1]}*! Stole {spoils}💳."

    # Update sheets
    attacker[3], defender[3] = str(aC), str(dC)
    update_row('Players', atk_i, attacker)
    update_row('Players', def_i, defender)
    append_row('CombatLog', [uid, defender[0], timestamp, result, str(spoils)])

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('attack', attack)
