# handlers/army.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.unit_manager import get_all_units_by_tier, get_unlocked_tier, UNITS
from config import TIER_UNLOCK
from sheets_service import get_rows
from utils.format_utils import section_header, format_bar
from utils.decorators import game_command

def _build_army_lines(uid: str):
    # Fetch player name
    players = get_rows('Players')[1:]
    commander = next((r[1] for r in players if r[0] == uid), "Commander")

    # Fetch your unit counts
    army_rows = get_rows('Army')[1:]
    counts = {key: 0 for key in UNITS}
    for r in army_rows:
        if r[0] == uid:
            counts[r[1]] = int(r[2])

    total_units = sum(counts.values())
    unlocked    = get_unlocked_tier(uid)
    all_units   = get_all_units_by_tier()

    lines = [
        f"🗡️ `/army` — *{commander}’s Army Overview*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 Total Forces: *{total_units}* units",
        ""
    ]

    for tier in sorted(all_units.keys()):
        if tier < unlocked:
            title = f"⚔️ Tier {tier} — Veteran"
        elif tier == unlocked:
            title = f"🆕 Tier {tier} — Available to Train"
        else:
            title = f"🔒 Tier {tier} — Locked"
        lines.append(section_header(title, pad_char="-", pad_count=3))
        lines.append("")

        if tier > unlocked:
            reqs = TIER_UNLOCK.get(tier, {})
            req_text = ", ".join(f"{b} Lv{l}" for b, l in reqs.items()) or "None"
            lines.append(f"Requires: {req_text}")
        else:
            for key, name, emoji, power, cost in all_units[tier]:
                cnt = counts.get(key, 0)
                if tier < unlocked:
                    # retired units
                    bar = format_bar(cnt, total_units or 1)
                    lines.append(f"{emoji} {name}: {cnt}  {bar}")
                else:
                    # current tier
                    lines.append(
                        f"{emoji} {name}: {cnt}   Pwr {power}   Cost "
                        f"{cost['c']}💳/{cost['m']}⛏️/{cost['e']}⚡"
                    )
        lines.append("")

    lines.append("🔄 Use `/army` again to refresh this overview.")
    return lines

@game_command
async def army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = "\n".join(_build_army_lines(uid))

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Refresh", callback_data="army"),
        InlineKeyboardButton("🏹 Attack",  callback_data="army_attack"),
        InlineKeyboardButton("🏗️ Build",   callback_data="army_build"),
    ]])

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def army_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "army":
        return await army(update, context)

async def army_attack_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "❗ **How to Attack:**\n"
            "`/attack <Commander> -u infantry:10 tanks:5 ...`\n"
            "`Optional flags:`\n"
            "  • `-s <count>` to send scouts first\n"
            "  • `--scout-only` to only scout\n"
            "  • `-c <CODE>` to cancel a pending attack\n"
        ),
        parse_mode=ParseMode.MARKDOWN
    )

async def army_build_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "❗ **How to Build:**\n"
            "`/build <BuildingType>`\n"
            "Example: `/build Bank` to upgrade your Bank by 1 level."
        ),
        parse_mode=ParseMode.MARKDOWN
    )

# Export handlers
handler           = CommandHandler('army', army)
callback_handler  = CallbackQueryHandler(army_button,        pattern="^army$")
attack_callback   = CallbackQueryHandler(army_attack_button, pattern="^army_attack$")
build_callback    = CallbackQueryHandler(army_build_button,  pattern="^army_build$")
