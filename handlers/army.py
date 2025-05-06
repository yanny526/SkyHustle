# handlers/army.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.unit_manager import get_all_units_by_tier, get_unlocked_tier, UNITS
from config import TIER_UNLOCK
from sheets_service import get_rows
from utils.format_utils import section_header

def format_cost(cost: dict) -> str:
    return f"{cost['c']}💳/{cost['m']}⛏️/{cost['e']}⚡"

@game_command
async def army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /army – show your army composition and tier unlocks
    """
    uid = str(update.effective_user.id)

    # Fetch player name
    players = get_rows('Players')[1:]
    game_name = next((r[1] for r in players if r[0] == uid), update.effective_user.first_name)

    # Fetch counts
    army_rows = get_rows('Army')[1:]
    counts = {key: 0 for key in UNITS}
    for r in army_rows:
        if r[0] == uid:
            counts[r[1]] = int(r[2])

    # Determine unlocked tier and units
    unlocked = get_unlocked_tier(uid)
    all_units = get_all_units_by_tier()

    # Build UI
    lines = [
        section_header(f"🏰 {game_name}’s Army 🏰", pad_char="=", pad_count=3),
        ""
    ]
    for tier in sorted(all_units.keys()):
        # Tier header
        if tier < unlocked:
            title = f"⚔️ Tier {tier} – Veteran"
        elif tier == unlocked:
            title = f"🆕 Tier {tier} – Available"
        else:
            title = f"🔒 Tier {tier} – Locked"
        lines.append(section_header(title, pad_char="-", pad_count=3))
        lines.append("")

        # Content per tier
        if tier > unlocked:
            reqs = TIER_UNLOCK.get(tier, {})
            req_text = " & ".join(f"{b} Lvl {l}" for b, l in reqs.items()) or "N/A"
            lines.append(f"Requires: {req_text}")
        else:
            for key, display, emoji, power, cost in all_units[tier]:
                cnt = counts.get(key, 0)
                if tier < unlocked:
                    lines.append(f"• {emoji} {display}: {cnt} _(retired)_")
                else:
                    lines.append(
                        f"• {emoji} {display}: {cnt}   Pwr {power}   Cost {format_cost(cost)}"
                    )
        lines.append("")

    # Send
    text = "\n".join(lines).rstrip()
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('army', army)
