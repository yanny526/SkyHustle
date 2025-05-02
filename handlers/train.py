# handlers/train.py

import time
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row

async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train <unit> <count> - train units instantly, deduct resources and update army count.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "❗ Usage: `/train <unit> <count>`\n"
            "Units: infantry, tanks, artillery\n"
            "Example: `/train infantry 5`",
            parse_mode='Markdown'
        )
        return

    unit_input = args[0].lower()
    # normalize unit type
    unit_alias = {
        'infantry': 'infantry',
        'tank': 'tanks',
        'tanks': 'tanks',
        'artillery': 'artillery'
    }
    if unit_input not in unit_alias:
        await update.message.reply_text(
            f"❌ Unknown unit *{args[0]}*.\nUnits: infantry, tanks, artillery",
            parse_mode='Markdown'
        )
        return

    unit = unit_alias[unit_input]
    try:
        count = int(args[1])
        if count <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("❌ Count must be a positive integer.")
        return

    # define costs per unit
    UNIT_COSTS = {
        'infantry': {'credits': 10, 'minerals': 5},
        'tanks': {'credits': 100, 'minerals': 50},
        'artillery': {'credits': 200, 'minerals': 100},
    }

    cost = UNIT_COSTS[unit]
    total_credits = cost['credits'] * count
    total_minerals = cost['minerals'] * count

    # fetch player resources
    players = get_rows('Players')
    player_row = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            player_row = (idx, row.copy())
            break
    if player_row is None:
        await update.message.reply_text("❗ You need to run `/start` first.")
        return

    prow_idx, prow = player_row
    credits = int(prow[3])
    minerals = int(prow[4])

    if credits < total_credits or minerals < total_minerals:
        await update.message.reply_text(
            f"❌ Insufficient resources.\n"
            f"Need {total_credits} 💳 and {total_minerals} ⛏️."
        )
        return

    # deduct resources
    prow[3] = str(credits - total_credits)
    prow[4] = str(minerals - total_minerals)
    update_row('Players', prow_idx, prow)

    # update army sheet
    army = get_rows('Army')
    army_row = None
    for idx, row in enumerate(army[1:], start=1):
        if row[0] == uid and row[1].lower() == unit:
            army_row = (idx, row.copy())
            break

    if army_row:
        aidx, arow = army_row
        current = int(arow[2])
        arow[2] = str(current + count)
        update_row('Army', aidx, arow)
    else:
        append_row('Army', [uid, unit, str(count)])

    # confirmation
    emoji_map = {'infantry': '👨‍✈️', 'tanks': '🛡️', 'artillery': '🚀'}
    emoji = emoji_map.get(unit, '')
    await update.message.reply_text(
        f"{emoji} Trained {count} {unit}! "
        f"Resources spent: {total_credits} 💳, {total_minerals} ⛏️."
    )

handler = CommandHandler('train', train)
