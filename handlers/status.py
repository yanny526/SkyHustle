# handlers/status.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from modules.upgrade_manager import complete_upgrades, get_pending_upgrades
from modules.building_manager import get_building_info
from modules.unit_manager import UNITS
from sheets_service import get_rows, update_row

# Constants for production rates per building level
MINERAL_RATE_PER_LVL = 20  # minerals per hour per Mine level
ENERGY_RATE_PER_LVL  = 10  # energy per hour per Power Plant level

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show your base status: resources, production, buildings, upgrades, and army."""
    uid = str(update.effective_user.id)
    now = int(time.time())

    # 1) Complete any finished building upgrades
    complete_upgrades(uid)

    # 2) Fetch player row and determine index for updates
    players = get_rows('Players')
    player_idx = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            player_idx = idx
            name = row[1]
            credits  = int(row[3])
            minerals = int(row[4])
            energy   = int(row[5])
            last_seen_ts = int(row[6]) if len(row) > 6 and row[6].isdigit() else now
            break
    else:
        return await update.message.reply_text("❗ Please run /start to join the game.")

    # 3) Calculate resource regeneration since last_seen
    delta = now - last_seen_ts
    binfo = get_building_info(uid)
    mineral_rate = binfo['Mine'] * MINERAL_RATE_PER_LVL
    energy_rate  = binfo['Power Plant'] * ENERGY_RATE_PER_LVL
    regen_min = int(delta * mineral_rate / 3600)
    regen_eng = int(delta * energy_rate  / 3600)

    # 4) Update player sheet with new resources and last_seen
    if regen_min or regen_eng:
        minerals += regen_min
        energy   += regen_eng
        new_row = [uid, name, row[2], str(credits), str(minerals), str(energy), str(now)]
        update_row('Players', player_idx, new_row)

    # 5) Start building the message lines
    lines = []

    # regeneration header
    if regen_min or regen_eng:
        lines.append(f"🌱 +{regen_min} Minerals, +{regen_eng} Energy\n")

    # base header
    lines.append(f"🏰 *Base Status for {name}*")
    lines.append(f"💳 {credits}   ⛏️ {minerals}   ⚡ {energy}\n")

    # buildings with levels and production/effects
    lines.append("🏗️ *Buildings:*" )
    lines.append(f"• ⛏️ Mine (Lvl {binfo['Mine']}) → +{mineral_rate} minerals/hr")
    lines.append(f"• ⚡ Power Plant (Lvl {binfo['Power Plant']}) → +{energy_rate} energy/hr")
    lines.append(f"• 🛡️ Barracks (Lvl {binfo['Barracks']}) → -{binfo['Barracks']*5}% train time")
    lines.append(f"• 🔧 Workshop (Lvl {binfo['Workshop']}) → +{binfo['Workshop']*2}% combat strength\n")

    # pending upgrades
    pend = get_pending_upgrades(uid)
    if pend:
        lines.append("⏳ *Upgrades in Progress:*" )
        for btype, target_lvl, remaining in pend:
            lines.append(f"• ⚡ {btype} → Lvl {target_lvl} ({remaining} remaining)")
        lines.append("")

    # army counts
    lines.append("⚔️ *Army:*" )
    army_rows = get_rows('Army')
    counts = { r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid }

    # group and display units by tier
    tiers = {}
    for key, (display, emoji, tier, _, _) in UNITS.items():
        tiers.setdefault(tier, []).append((display, emoji, key))

    for tier in sorted(tiers):
        lines.append(f"*Tier {tier} Units:*" )
        for display, emoji, key in sorted(tiers[tier], key=lambda x: x[0]):
            cnt = counts.get(key, 0)
            lines.append(f"• {emoji} {display}: {cnt}")
        lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

# register handler
handler = CommandHandler('status', status)
