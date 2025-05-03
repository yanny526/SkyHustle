# handlers/status.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from modules.upgrade_manager import complete_upgrades, get_pending_upgrades
from modules.building_manager import get_building_info
from modules.unit_manager import UNITS
from sheets_service import get_rows

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /status – show your base status, resources, buildings, upgrades, and army counts """
    uid = str(update.effective_user.id)

    # 1) Complete any finished building upgrades
    complete_upgrades(uid)

    # 2) Fetch player resources row
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

    # 3) Buildings
    binfo = get_building_info(uid)
    for btype, lvl in binfo.items():
        lines.append(f" • {btype}: Lvl {lvl}")
    lines.append("")

    # 4) Upgrades In Progress (always show this block)
    pend = get_pending_upgrades(uid)
    lines.append("⏳ *Upgrades In Progress:*")
    if pend:
        for btype, nxt, rem in pend:
            lines.append(f" • {btype} → Lvl {nxt} ({rem} remaining)")
    else:
        lines.append(" • None")
    lines.append("")

    # 5) Army counts
    army_rows = get_rows('Army')
    counts = { row[1]: int(row[2]) for row in army_rows[1:] if row[0] == uid }

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

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler('status', status)
