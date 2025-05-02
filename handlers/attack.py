# handlers/attack.py

import time
import random
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <CommanderName> – attack another commander by their unique name.
    """
    user = update.effective_user
    uid = str(user.id)

    # 1) Tick resources and complete any finished upgrades
    tick_resources(uid)
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(f"✅ {b} upgrade complete! Now Lvl {lvl}."
                         for b, lvl in done)
        await update.message.reply_text(msgs)

    args = context.args
    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <CommanderName>`\n"
            "Example: `/attack IronLegion`",
            parse_mode="Markdown"
        )

    target_name = args[0]
    # Load all players
    players = get_rows('Players')
    attacker_row = defender_row = None
    atk_idx = def_idx = None

    for idx, row in enumerate(players[1:], start=1):
        # row = [user_id, commander_name, telegram_username, credits, minerals, energy, last_seen]
        if row[0] == uid:
            attacker_row, atk_idx = row.copy(), idx
        if row[1] == target_name:
            defender_row, def_idx = row.copy(), idx

    # Validate target exists
    if not defender_row:
        return await update.message.reply_text(
            f"❌ Commander *{target_name}* not found. "
            "Make sure they’ve set their name with `/setname`.",
            parse_mode="Markdown"
        )

    # Prevent self-attack
    if defender_row[0] == uid:
        return await update.message.reply_text(
            "❌ You cannot attack yourself!",
            parse_mode="Markdown"
        )

    # Commander names
    attacker_name = attacker_row[1] or user.first_name

    # Parse and update credits
    atk_credits = int(attacker_row[3])
    def_credits = int(defender_row[3])

    # Calculate power from army
    def calc_power(urow):
        total = 0
        for r in get_rows('Army')[1:]:
            if r[0] != urow[0]:
                continue
            count = int(r[2])
            unit = r[1].lower()
            if unit == 'infantry':
                total += count * 10
            elif unit == 'tanks':
                total += count * 50
            elif unit == 'artillery':
                total += count * 100
        return total

    atk_power = calc_power(attacker_row)
    def_power = calc_power(defender_row)

    # Randomized rolls
    atk_roll = atk_power * random.uniform(0.9, 1.1)
    def_roll = def_power * random.uniform(0.9, 1.1)

    timestamp = int(time.time())
    if atk_roll > def_roll:
        result = 'win'
        spoils = max(1, def_credits // 10)
        atk_credits += spoils
        def_credits -= spoils
        msg = (
            f"🏆 *{attacker_name}* defeated *{target_name}*!\n"
            f"Stole {spoils}💳."
        )
    else:
        result = 'loss'
        spoils = max(1, atk_credits // 20)
        atk_credits -= spoils
        def_credits += spoils
        msg = (
            f"💥 *{attacker_name}* was defeated by *{target_name}*!\n"
            f"{target_name} stole {spoils}💳 from you."
        )

    # Update Players sheet
    attacker_row[3] = str(atk_credits)
    defender_row[3] = str(def_credits)
    update_row('Players', atk_idx, attacker_row)
    update_row('Players', def_idx, defender_row)

    # Log combat
    append_row('CombatLog', [
        uid,
        defender_row[0],  # target's user_id
        str(timestamp),
        result,
        str(spoils)
    ])

    # Send result
    await update.message.reply_text(msg, parse_mode="Markdown")

handler = CommandHandler('attack', attack)
