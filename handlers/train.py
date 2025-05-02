# handlers/train.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from modules.unit_manager import get_unlocked_tier, UNITS
import re

@game_command
async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train <unit> <count> - train units. Accepts snake_case, CamelCase, or display name.
    Only the current unlocked tier is allowed.
    """
    uid = str(update.effective_user.id)
    args = context.args

    if len(args) < 2:
        return await update.message.reply_text(
            "❗ Usage: `/train <unit> <count>`",
            parse_mode=ParseMode.MARKDOWN
        )

    raw_key = args[0]
    # Normalize input to match unit keys
    def generate_aliases(k, info):
        display = info[0]
        return {
            k.lower(),
            k.replace("_", "").lower(),
            display.replace(" ", "").lower()
        }

    matches = [k for k, info in UNITS.items() if raw_key.lower() in generate_aliases(k, info)]
    if not matches:
        return await update.message.reply_text(
            f"❌ Unknown unit *{raw_key}*.", parse_mode=ParseMode.MARKDOWN
        )
    if len(matches) > 1:
        return await update.message.reply_text(
            f"❌ Ambiguous unit name *{raw_key}* matches: {', '.join(matches)}.",
            parse_mode=ParseMode.MARKDOWN
        )
    key = matches[0]

    # Parse count
    try:
        cnt = int(args[1])
        if cnt < 1:
            raise ValueError
    except ValueError:
        return await update.message.reply_text("❌ Count must be a positive integer.")

    name, emoji, tier, power, cost = UNITS[key]

    # Check tier
    unlocked = get_unlocked_tier(uid)
    if tier != unlocked:
        return await update.message.reply_text(
            f"❌ {name} is Tier {tier}. You have unlocked Tier {unlocked}.",
            parse_mode=ParseMode.MARKDOWN
        )

    # Calculate total cost
    totC = cost['c'] * cnt
    totM = cost['m'] * cnt
    totE = cost['e'] * cnt

    # Fetch player resources
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

    # Deduct resources
    prow[3], prow[4], prow[5] = str(creds - totC), str(minr - totM), str(engy - totE)
    update_row('Players', idx, prow)

    # Update army counts
    army = get_rows('Army')
    found = None
    for ai, row in enumerate(army[1:], start=1):
        if row[0] == uid and row[1] == key:
            found = (ai, row.copy())
            break

    if found:
        ai, arow = found
        arow[2] = str(int(arow[2]) + cnt)
        update_row('Army', ai, arow)
    else:
        append_row('Army', [uid, key, str(cnt)])

    await update.message.reply_text(
        f"{emoji} Trained {cnt}×{name}! Spent {totC}💳 {totM}⛏️ {totE}⚡.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler('train', train)
```
