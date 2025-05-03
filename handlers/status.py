# handlers/status.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from modules.building_manager import get_building_info
from modules.unit_manager import UNITS
from sheets_service import get_rows

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /status – show your base status, resources, buildings, and army counts """
    uid = str(update.effective_user.id)

    # Fetch player resources row
    players = get_rows('Players')
    for row in players[1:]:
        if row[0] == uid:
            name = row[1]
            credits, minerals, energy = map(int, (row[3], row[4], row[5]))
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    lines = [
        f"🏰 *Base Status for {name}*\n",
        f"💳 Credits: {credits}   ⛏️ Minerals: {minerals}   ⚡ Energy: {energy}\n",
        "🏗️ *Buildings:*"
    ]

    # Buildings
    binfo = get_building_info(uid)
    for btype, lvl in binfo.items():
        lines.append(f" • {btype}: Lvl {lvl}")
    lines.append("")

    # Army counts
    army_rows = get_rows('Army')
    counts = {}
    for row in army_rows[1:]:
        if row[0] == uid:
            counts[row[1]] = int(row[2])

    lines.append("⚔️ *Army:*")
    # Group units by tier
    tiers = {}
    for key, info in UNITS.items():
        display, emoji, tier, _, _ = info
        tiers.setdefault(tier, []).append((display, emoji, key))

    for tier in sorted(tiers):
        lines.append(f"*Tier {tier} Units:*")
        for display, emoji, key in sorted(tiers[tier], key=lambda x: x[0]):
            cnt = counts.get(key, 0)
            lines.append(f" • {emoji} {display}: {cnt}")
        lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('status', status)
