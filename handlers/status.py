# handlers/status.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss
from utils.decorators import game_command
from config import BUILDING_MAX_LEVEL

@game_command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status - show current base status, marking MAXED buildings at cap.
    """
    user = update.effective_user
    uid = str(user.id)
    now = time.time()

    # Fetch player row
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

    # Fetch building levels and pending upgrades
    building_rows = get_rows('Buildings')[1:]
    buildings = {b: 0 for b in BUILDING_MAX_LEVEL}
    upgrades = {}
    for row in building_rows:
        if row[0] != uid:
            continue
        btype = row[1]
        lvl = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
        buildings[btype] = lvl
        if len(row) > 3 and row[3]:
            try:
                end_ts = float(row[3])
                if end_ts > now:
                    upgrades[btype] = (lvl + 1, end_ts)
            except ValueError:
                pass

    # Fetch army counts
    army_counts = {'infantry': 0, 'tanks': 0, 'artillery': 0}
    for row in get_rows('Army')[1:]:
        if row[0] != uid:
            continue
        army_counts[row[1].lower()] = int(row[2])

    # Begin status text
    text = [
        f"🏰 *Base Status* 🏰",
        f"Commander: *{commander_name}*",
        "",
        f"💳 Credits: {credits}   ⛏️ Minerals: {minerals}   ⚡ Energy: {energy}",
        ""
    ]

    # Buildings section
    text.append("🏢 *Buildings*")
    # Define display parameters for each building
    display_info = [
        ('Mine', '⛏️', 20, 'minerals/hr'),
        ('Power Plant', '⚡', 10, 'energy/hr'),
        ('Barracks', '🛡️', 5, '% train time reduction'),
        ('Workshop', '🔧', 2, '% combat boost'),
    ]
    for btype, emoji, factor, unit_desc in display_info:
        lvl = buildings.get(btype, 0)
        max_lvl = BUILDING_MAX_LEVEL.get(btype, None)
        if max_lvl is not None and lvl >= max_lvl:
            text.append(f" • {emoji} {btype} (Lvl {lvl}) – *MAXED* ")
        else:
            if btype in ('Mine', 'Power Plant'):
                rate = lvl * factor
                text.append(f" • {emoji} {btype} (Lvl {lvl}) → +{rate} {unit_desc}")
            elif btype == 'Barracks':
                reduction = lvl * factor
                text.append(f" • {emoji} {btype} (Lvl {lvl}) → –{reduction}{unit_desc}")
            else:  # Workshop
                boost = lvl * factor
                text.append(f" • {emoji} {btype} (Lvl {lvl}) → +{boost}{unit_desc}")

    # Upgrades in progress
    text.append("")
    text.append("🔄 *Upgrades in progress*")
    if upgrades:
        for btype, (next_lvl, end_ts) in upgrades.items():
            rem = format_hhmmss(int(end_ts - now))
            emoji = dict((bt, em) for bt, em, *_ in display_info).get(btype, '')
            text.append(f" • {emoji} {btype} → Lvl {next_lvl} ({rem} remaining)")
    else:
        text.append(" • None")

    # Army section
    text.append("")
    text.append("🛡️ *Army*")
    text.append(f" • 👨‍✈️ Infantry: {army_counts['infantry']}")
    text.append(f" • 🛡️ Tanks: {army_counts['tanks']}")
    text.append(f" • 🚀 Artillery: {army_counts['artillery']}")

    await update.message.reply_text("\n".join(text), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('status', status)
