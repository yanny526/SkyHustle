# handlers/train.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command

@game_command
async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train <unit> <count> - train units (tick & upgrades via decorator).
    """
    uid = str(update.effective_user.id)
    args = context.args

    if len(args) < 2:
        return await update.message.reply_text(
            "❗ Usage: `/train <unit> <count>`\n"
            "Infantry(1⚡), Tanks(5⚡), Artillery(10⚡)",
            parse_mode=ParseMode.MARKDOWN
        )

    unit_map = {'infantry': 'infantry', 'tank': 'tanks', 'tanks': 'tanks', 'artillery': 'artillery'}
    u = args[0].lower()
    if u not in unit_map:
        return await update.message.reply_text(
            f"❌ Unknown unit *{args[0]}*.",
            parse_mode=ParseMode.MARKDOWN
        )
    unit = unit_map[u]

    try:
        cnt = int(args[1])
        if cnt < 1:
            raise ValueError
    except ValueError:
        return await update.message.reply_text("❌ Count must be a positive integer.")

    COSTS = {
        'infantry': {'c': 10, 'm': 5, 'e': 1},
        'tanks':    {'c': 100, 'm': 50, 'e': 5},
        'artillery':{'c': 200, 'm': 100, 'e': 10},
    }
    cost = COSTS[unit]
    totC, totM, totE = cost['c']*cnt, cost['m']*cnt, cost['e']*cnt

    # Fetch player
    rows = get_rows('Players')
    for pi, row in enumerate(rows[1:], start=1):
        if row[0] == uid:
            prow, idx = row.copy(), pi
            break
    else:
        return await update.message.reply_text("❗ Run /start first.")

    creds, minr, engy = map(int, (prow[3], prow[4], prow[5]))
    if creds < totC or minr < totM or engy < totE:
        return await update.message.reply_text(f"❌ Need {totC}💳 {totM}⛏️ {totE}⚡.")

    # Deduct
    prow[3], prow[4], prow[5] = str(creds - totC), str(minr - totM), str(engy - totE)
    update_row('Players', idx, prow)

    # Update army
    army = get_rows('Army')
    found = None
    for ai, row in enumerate(army[1:], start=1):
        if row[0] == uid and row[1] == unit:
            found = (ai, row.copy())
            break

    if found:
        ai, arow = found
        arow[2] = str(int(arow[2]) + cnt)
        update_row('Army', ai, arow)
    else:
        append_row('Army', [uid, unit, str(cnt)])

    emoji = {'infantry': '👨‍✈️', 'tanks': '🛡️', 'artillery': '🚀'}[unit]
    await update.message.reply_text(
        f"{emoji} Trained {cnt}×{unit}! Spent {totC}💳 {totM}⛏️ {totE}⚡."
    )

handler = CommandHandler('train', train)
