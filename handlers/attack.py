# handlers/attack.py

import time
import random
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from modules.unit_manager import UNITS

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
            f"❌ Commander *{target}* not found.", parse_mode=ParseMode.MARKDOWN
        )
    if defender[0] == uid:
        return await update.message.reply_text(
            "❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN
        )

    # Deduct energy
    energy = int(attacker[5])
    if energy < 5:
        return await update.message.reply_text("❌ Not enough energy. Need 5⚡.")
    attacker[5] = str(energy - 5)
    update_row('Players', atk_i, attacker)

    # Compute army power
    def power(urow):
        total = 0
        for r in get_rows('Army')[1:]:
            if r[0] != urow[0]:
                continue
            unit_key = r[1]
            count = int(r[2])
            _, _, _, unit_power, _ = UNITS.get(unit_key, (None, None, None, 0, None))
            total += count * unit_power
        return total

    atk_roll = power(attacker) * random.uniform(0.9, 1.1)
    def_roll = power(defender) * random.uniform(0.9, 1.1)

    timestamp = str(int(time.time()))
    if atk_roll > def_roll:
        result = 'win'
        spoils = max(1, int(defender[3]) // 10)
        attacker_credits = int(attacker[3]) + spoils
        defender_credits = int(defender[3]) - spoils
        msg = f"🏆 *{attacker[1]}* defeated *{defender[1]}*! Stole {spoils}💳."
    else:
        result = 'loss'
        spoils = max(1, int(attacker[3]) // 20)
        attacker_credits = int(attacker[3]) - spoils
        defender_credits = int(defender[3]) + spoils
        msg = f"💥 *{attacker[1]}* was defeated by *{defender[1]}*! Lost {spoils}💳."

    # Update credits
    attacker[3], defender[3] = str(attacker_credits), str(defender_credits)
    update_row('Players', atk_i, attacker)
    update_row('Players', def_i, defender)
    append_row('CombatLog', [uid, defender[0], timestamp, result, str(spoils)])

    # Send the battle result
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # QUEST PROGRESSION STEP 5: First Attack Reward
    # Only if they have completed step4
    players = get_rows('Players')
    header = players[0]
    for pi, prow in enumerate(players[1:], start=1):
        if prow[0] == uid:
            # Ensure prow has correct length
            while len(prow) < len(header): prow.append("")
            progress = prow[7]
            break
    else:
        return

    if progress == 'step4':
        # grant 5 infantry and 1 tank
        # update energy counts in Army sheet
        army_rows = get_rows('Army')
        # helper to add units
        def add_unit(unit_key, quantity):
            for ai, arow in enumerate(army_rows[1:], start=1):
                if arow[0] == uid and arow[1] == unit_key:
                    # update existing row
                    arow[2] = str(int(arow[2]) + quantity)
                    update_row('Army', ai, arow)
                    return
            # else append new row
            append_row('Army', [uid, unit_key, str(quantity)])

        add_unit('infantry', 5)
        add_unit('tanks', 1)

        # update progress
        prow[7] = 'step5'
        update_row('Players', pi, prow)

        reward_msg = (
            "🎉 Mission Complete!\n"
            "✅ Your first conquest is won!\n"
            "💂 +5 Infantry and 🏎️ +1 Tank have joined your army.\n\n"
            "Next mission: `/leaderboard` – see where you stand among commanders."
        )
        await update.message.reply_text(reward_msg, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('attack', attack)
