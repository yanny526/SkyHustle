# handlers/status.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status - show current base status, notify of completed upgrades, tick resources.
    """
    user = update.effective_user
    uid = str(user.id)

    # 1) Tick resources
    added = tick_resources(uid)

    # 2) Complete any finished upgrades
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(f"✅ {btype} upgrade complete! Now Lvl {lvl}."
                         for btype, lvl in done)
        await update.message.reply_text(msgs)

    now = time.time()

    # 3) Fetch player row
    players = get_rows('Players')
    commander_name = user.first_name
    credits = minerals = energy = 0
    for row in players[1:]:
        if row[0] == uid:
            commander_name = row[1] or commander_name
            credits = int(row[3])
            minerals = int(row[4])
            energy = int(row[5])
            break

    # 4) Fetch buildings & pending upgrades
    buildings = {'Mine': 0, 'Power Plant': 0, 'Barracks': 0, 'Workshop': 0}
    upgrades = {}  # building -> (next_level, end_ts)
    for row in get_rows('Buildings')[1:]:
        if row[0] != uid:
            continue
        # Safely extract level
        lvl = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
        btype = row[1]
        buildings[btype] = lvl

        # Only check upgrade_end_ts if column exists
        if len(row) > 3 and row[3]:
            try:
                end_ts = float(row[3])
                if end_ts > now:
                    upgrades[btype] = (lvl + 1, end_ts)
            except ValueError:
                # Malformed timestamp; skip
                pass

    # 5) Fetch army
    army_counts = {'infantry': 0, 'tanks': 0, 'artillery': 0}
    for row in get_rows('Army')[1:]:
        if row[0] != uid:
            continue
        unit = row[1].lower()
        army_counts[unit] = int(row[2])

    # 6) Build and send status message
    text = [
        f"🏰 *Base Status* 🏰",
        f"Commander: *{commander_name}*",
        "",
        f"💳 Credits: {credits}   ⛏️ Minerals: {minerals}   ⚡ Energy: {energy}",
    ]
    if added['minerals'] or added['energy']:
        text.append(f"🌱 +{added['minerals']} Minerals, +{added['energy']} Energy")

    text += [
        "",
        "🏢 *Buildings*",
        f" • ⛏️ Mine (Lvl {buildings['Mine']}) → +{buildings['Mine'] * 20} Minerals/hr",
        f" • ⚡ Power Plant (Lvl {buildings['Power Plant']}) → +{buildings['Power Plant'] * 10} Energy/hr",
        f" • 🛡️ Barracks (Lvl {buildings['Barracks']}) → –{buildings['Barracks'] * 5}% train time",
        f" • 🔧 Workshop (Lvl {buildings['Workshop']}) → +{buildings['Workshop'] * 2}% combat boost",
        "",
        "🔄 *Upgrades in progress*"
    ]
    if upgrades:
        for btype, (next_lvl, end_ts) in upgrades.items():
            rem = format_hhmmss(int(end_ts - now))
            emoji = {'Mine': '⛏️', 'Power Plant': '⚡',
                     'Barracks': '🛡️', 'Workshop': '🔧'}[btype]
            text.append(f" • {emoji} {btype} → Lvl {next_lvl} ({rem} remaining)")
    else:
        text.append(" • None")

    text += [
        "",
        "🛡️ *Army*",
        f" • 👨‍✈️ Infantry: {army_counts['infantry']}",
        f" • 🛡️ Tanks: {army_counts['tanks']}",
        f" • 🚀 Artillery: {army_counts['artillery']}",
    ]

    await update.message.reply_text("\n".join(text), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('status', status)
