# handlers/status.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.upgrade_manager import get_pending_upgrades
from modules.building_manager import get_building_info
from modules.unit_manager import UNITS
from sheets_service import get_rows

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /status - show current base status, resources, buildings, upgrades, and army counts """
    uid = str(update.effective_user.id)

    # Player resources
    players = get_rows('Players')[1:]
    creds = mins = engy = None
    commander = None
    for row in players:
        if row[0] == uid:
            commander = row[1]
            creds, mins, engy = map(int, (row[3], row[4], row[5]))
            break
    if creds is None:
        return await update.message.reply_text("❗ Run /start first.")

    lines = []
    lines.append("🏰 *Base Status* 🏰")
    lines.append(f"Commander: {commander}")
    lines.append(f"💳 Credits: {creds}   ⛏️ Minerals: {mins}   ⚡ Energy: {engy}")
    lines.append("")

    # Buildings
    lines.append("🏢 *Buildings*")
    for bname, lvl, bonus in get_building_info(uid):
        lines.append(f"• {bname} (Lvl {lvl}) → {bonus}")
    lines.append("")

    # Upgrades in progress
    pending = get_pending_upgrades(uid)
    lines.append("🔧 *Upgrades in progress*")
    if pending:
        for name, target_lvl, remaining in pending:
            lines.append(f"• {name} → Lvl {target_lvl} ({remaining} remaining)")
    else:
        lines.append("• None")
    lines.append("")

    # Army counts
    army_rows = get_rows('Army')[1:]
    counts = {key: 0 for key in UNITS.keys()}
    for row in army_rows:
        if row[0] == uid and row[1] in counts:
            counts[row[1]] = int(row[2])

    lines.append("🪖 *Army* ")
    # Show each unit in tier order
    # Sort by tier then display name
    tiers = {}
    for key, info in UNITS.items():
        _, emoji, tier, _, _ = info
        tiers.setdefault(tier, []).append((key, info))
    for tier in sorted(tiers.keys()):
        for key, info in sorted(tiers[tier], key=lambda x: x[1][0]):
            display, emoji, *_ = info
            cnt = counts.get(key, 0)
            lines.append(f"• {emoji} {display}: {cnt}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('status', status)
