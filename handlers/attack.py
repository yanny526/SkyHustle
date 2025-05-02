# handlers/attack.py

import time
import random
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <user_id> - attack another commander by their Telegram user_id.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args

    if not args:
        await update.message.reply_text(
            "❗ Usage: `/attack <user_id>`\n"
            "Example: `/attack 123456789`",
            parse_mode="Markdown"
        )
        return

    target_id = args[0]
    if target_id == uid:
        await update.message.reply_text("❌ You cannot attack yourself!")
        return

    # Load players
    players = get_rows('Players')
    attacker_row = defender_row = None
    atk_idx = def_idx = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            attacker_row, atk_idx = row.copy(), idx
        if row[0] == target_id:
            defender_row, def_idx = row.copy(), idx

    if not defender_row:
        await update.message.reply_text(
            "❌ Commander not found. Use /status to find friend IDs.",
            parse_mode="Markdown"
        )
        return

    # Parse credits
    atk_credits = int(attacker_row[3])
    def_credits = int(defender_row[3])

    # Load armies
    army = get_rows('Army')
    def get_power(urow):
        inf = tanks = art = 0
        for r in army[1:]:
            if r[0] == urow[0]:
                if r[1] == 'infantry':
                    inf = int(r[2])
                elif r[1] == 'tanks':
                    tanks = int(r[2])
                elif r[1] == 'artillery':
                    art = int(r[2])
        return inf * 10 + tanks * 50 + art * 100

    atk_power = get_power(attacker_row)
    def_power = get_power(defender_row)

    # Apply randomness
    atk_roll = atk_power * random.uniform(0.9, 1.1)
    def_roll = def_power * random.uniform(0.9, 1.1)

    timestamp = int(time.time())
    if atk_roll > def_roll:
        result = 'win'
        spoils = max(1, def_credits // 10)
        atk_credits += spoils
        def_credits -= spoils
        msg = f"🏆 Victory! You stole {spoils} 💳 from Commander {target_id}."
    else:
        result = 'loss'
        spoils = max(1, atk_credits // 20)
        atk_credits -= spoils
        def_credits += spoils
        msg = f"💥 Defeat! Commander {target_id} stole {spoils} 💳 from you."

    # Update player resources
    attacker_row[3] = str(atk_credits)
    defender_row[3] = str(def_credits)
    update_row('Players', atk_idx, attacker_row)
    update_row('Players', def_idx, defender_row)

    # Log combat
    append_row('CombatLog', [
        uid, target_id, str(timestamp), result, str(spoils)
    ])

    await update.message.reply_text(msg)

handler = CommandHandler('attack', attack)
