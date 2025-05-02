# handlers/build.py

import time
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, append_row, update_row
from utils.time_utils import format_hhmmss

# Mapping user input to sheet titles and emojis
BUILDINGS = {
    'mine':        ('Mine',        '⛏️'),
    'powerplant':  ('Power Plant', '⚡'),
    'power plant':('Power Plant', '⚡'),
    'barracks':    ('Barracks',    '🛡️'),
    'workshop':    ('Workshop',    '🔧'),
}

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build <building> - start an upgrade for the specified building.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args
    now = time.time()

    if not args:
        await update.message.reply_text(
            "❗ Usage: `/build <building>`\n"
            "Available: mine, powerplant, barracks, workshop",
            parse_mode='Markdown'
        )
        return

    key = args[0].lower()
    if key not in BUILDINGS:
        await update.message.reply_text(
            f"❌ Unknown building *{args[0]}*.\n"
            "Valid options: mine, powerplant, barracks, workshop",
            parse_mode='Markdown'
        )
        return

    btype, emoji = BUILDINGS[key]

    # Fetch player row
    players = get_rows('Players')
    player_row = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            player_row = (idx, row.copy())
            break
    if player_row is None:
        await update.message.reply_text(
            "❗ You need to run `/start` first."
        )
        return
    prow_idx, prow = player_row
    credits = int(prow[3])
    minerals = int(prow[4])

    # Fetch building row (if exists)
    b_rows = get_rows('Buildings')
    b_row = None
    for idx, row in enumerate(b_rows[1:], start=1):
        if row[0] == uid and row[1] == btype:
            b_row = (idx, row.copy())
            break

    current_lvl = int(b_row[1][2]) if b_row else 0
    # Check existing upgrade
    if b_row and len(b_row[1]) > 3 and b_row[1][3]:
        end_ts = float(b_row[1][3])
        if end_ts > now:
            rem = format_hhmmss(int(end_ts - now))
            await update.message.reply_text(
                f"⏳ {emoji} {btype} upgrade to Lvl {current_lvl+1} "
                f"is already in progress ({rem} remaining)."
            )
            return

    # Determine cost & time
    L = current_lvl + 1
    if btype == 'Mine':
        cost_credits = 100
        cost_minerals = 50 * L
        time_min = 30 * L
    elif btype == 'Power Plant':
        cost_credits = 100
        cost_minerals = 30 * L
        time_min = 20 * L
    elif btype == 'Barracks':
        cost_credits = 150
        cost_minerals = 70 * L
        time_min = 45 * L
    else:  # Workshop
        cost_credits = 200
        cost_minerals = 100 * L
        time_min = 60 * L

    # Check resources
    if credits < cost_credits or minerals < cost_minerals:
        await update.message.reply_text(
            "❌ Insufficient resources.\n"
            f"Need {cost_credits} 💳 and {cost_minerals} ⛏️."
        )
        return

    # Deduct resources
    prow[3] = str(credits - cost_credits)
    prow[4] = str(minerals - cost_minerals)
    update_row('Players', prow_idx, prow)

    # Schedule upgrade
    end_ts = now + time_min * 60
    if b_row:
        bidx, brow = b_row
        brow[3] = str(end_ts)
        update_row('Buildings', bidx, brow)
    else:
        append_row('Buildings', [uid, btype, str(current_lvl), str(end_ts)])

    await update.message.reply_text(
        f"🔨 Upgrading {emoji} *{btype}* to Lvl {L}!\n"
        f"Cost: {cost_credits} 💳 + {cost_minerals} ⛏️\n"
        f"Complete in: {format_hhmmss(time_min*60)}",
        parse_mode='Markdown'
    )

handler = CommandHandler('build', build)
