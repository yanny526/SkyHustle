# handlers/army.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.unit_manager import get_all_units_by_tier, get_unlocked_tier, UNITS, TIER_UNLOCK
from sheets_service import get_rows

def format_cost(cost: dict) -> str:
    return f"{cost['c']}💳/{cost['m']}⛏️/{cost['e']}⚡"

async def army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /army - show your army counts and tier unlocks """
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name

    # Get current counts
    army_rows = get_rows('Army')[1:]
    counts = {key: 0 for key in UNITS.keys()}
    for row in army_rows:
        if row[0] != uid:
            continue
        counts[row[1]] = int(row[2])

    # Determine tiers
    unlocked = get_unlocked_tier(uid)
    all_units = get_all_units_by_tier()

    lines = [f"🎖️ *{name}’s Army*", ""]
    for tier in sorted(all_units.keys()):
        if tier < unlocked:
            status = f"*Tier {tier} – Expired*"
        elif tier == unlocked:
            status = f"*Tier {tier} – Available*"
        else:
            status = f"*Tier {tier} – Locked*"
        lines.append(status)

        if tier == unlocked:
            # Show available units
            for key, display, emoji, power, cost in all_units[tier]:
                cnt = counts.get(key, 0)
                lines.append(
                    f" • {emoji} {display}: {cnt}  (Pwr {power} | Cost {format_cost(cost)})"
                )
        elif tier < unlocked:
            # Show expired units
            for key, display, emoji, power, cost in all_units[tier]:
                cnt = counts.get(key, 0)
                lines.append(f" • {emoji} {display}: {cnt}  _(untrainable)_")
        else:
            # Show unlock requirements
            reqs = TIER_UNLOCK[tier]
            req_text = ", ".join(f"{b}≥Lvl{l}" for b, l in reqs.items())
            lines.append(f" Requires {req_text}")
        lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('army', army)
