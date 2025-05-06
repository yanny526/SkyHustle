# handlers/army.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.unit_manager import get_all_units_by_tier, get_unlocked_tier, UNITS
from config import TIER_UNLOCK
from sheets_service import get_rows
from utils.format_utils import section_header, format_bar

@game_command
async def army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /army – show your army overview & tier breakdown
    """
    uid = str(update.effective_user.id)

    # Fetch player name
    players = get_rows('Players')[1:]
    commander = next((r[1] for r in players if r[0] == uid), update.effective_user.first_name)

    # Fetch your unit counts
    rows = get_rows('Army')[1:]
    counts = {key: 0 for key in UNITS}
    for r in rows:
        if r[0] == uid:
            counts[r[1]] = int(r[2])

    # Total units
    total_units = sum(counts.values())

    # Determine which tier is unlocked
    unlocked = get_unlocked_tier(uid)
    all_units = get_all_units_by_tier()

    lines = [
        section_header(f"📋 {commander}’s Army Overview", pad_char="=", pad_count=3),
        f"Total Forces: {total_units} units",
        ""
    ]

    for tier in sorted(all_units.keys()):
        # Tier title
        if tier < unlocked:
            title = f"⚔️ Tier {tier} — Veteran"
        elif tier == unlocked:
            title = f"🆕 Tier {tier} — You Can Train"
        else:
            title = f"🔒 Tier {tier} — Locked"
        lines.append(section_header(title, pad_char="-", pad_count=3))

        # Content
        if tier > unlocked:
            reqs = TIER_UNLOCK.get(tier, {})
            req_text = ", ".join(f"{b} Lv{l}" for b, l in reqs.items()) or "None"
            lines.append(f"Requires: {req_text}")
        else:
            for key, name, emoji, power, cost in all_units[tier]:
                cnt = counts.get(key, 0)
                bar = format_bar(cnt, total_units or 1)
                if tier < unlocked:
                    lines.append(f"{emoji} {name}: {cnt}  {bar}")
                else:
                    lines.append(
                        f"{emoji} {name}: {cnt}  Pwr {power}  Cost {cost['c']}💳/{cost['m']}⛏️/{cost['e']}⚡"
                    )
        lines.append("")

    # If current tier is available, offer quick train button
    train_btn = None
    if unlocked in all_units:
        train_btn = InlineKeyboardButton(f"Train Tier {unlocked}", callback_data=f"train_tier_{unlocked}")

    reply_markup = InlineKeyboardMarkup([[train_btn]]) if train_btn else None

    text = "\n".join(lines).rstrip()
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

handler = CommandHandler('army', army)
