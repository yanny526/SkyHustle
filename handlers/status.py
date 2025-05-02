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

    # 1) Resource tick
    added = tick_resources(uid)

    # 2) Complete any finished upgrades
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(f"✅ {btype} upgrade complete! Now Lvl {lvl}."
                          for btype, lvl in done)
        await update.message.reply_text(msgs)

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

    # Buildings & upgrades
    buildings = { 'Mine':0, 'Power Plant':0, 'Barracks':0, 'Workshop':0 }
    upgrades = {}
    for row in get_rows('Buildings')[1:]:
        if row[0] != uid: continue
        b, lvl = row[1], int(row[2])
        buildings[b] = lvl
        if row[3]:
            et = float(row[3])
            if et>now:
                upgrades[b] = (lvl+1, et)

    # Army
    army = {'infantry':0,'tanks':0,'artillery':0}
    for row in get_rows('Army')[1:]:
        if row[0]!=uid: continue
        army[row[1]] = int(row[2])

    # Build text
    text = [
        f"🏰 *Base Status* 🏰",
        f"Commander: *{commander_name}*",
        "",
        f"💳 Credits: {credits}   ⛏️ Minerals: {minerals}   ⚡ Energy: {energy}",
    ]
    if added['minerals'] or added['energy']:
        text.append(
            f"🌱 +{added['minerals']} Minerals, +{added['energy']} Energy"
        )
    text += [
        "",
        "🏢 *Buildings*",
        f" • ⛏️ Mine (Lvl {buildings['Mine']}) → +{buildings['Mine']*20} Minerals/hr",
        f" • ⚡ Power Plant (Lvl {buildings['Power Plant']}) → +{buildings['Power Plant']*10} Energy/hr",
        f" • 🛡️ Barracks (Lvl {buildings['Barracks']}) → –{buildings['Barracks']*5}% train time",
        f" • 🔧 Workshop (Lvl {buildings['Workshop']}) → +{buildings['Workshop']*2}% combat boost",
        "",
        "🔄 *Upgrades in progress*"
    ]
    if upgrades:
        for b,(nl,et) in upgrades.items():
            rem = format_hhmmss(int(et-now))
            em = {'Mine':'⛏️','Power Plant':'⚡','Barracks':'🛡️','Workshop':'🔧'}[b]
            text.append(f" • {em} {b} → Lvl {nl} ({rem} remaining)")
    else:
        text.append(" • None")
    text += [
        "",
        "🛡️ *Army*",
        f" • 👨‍✈️ Infantry: {army['infantry']}",
        f" • 🛡️ Tanks: {army['tanks']}",
        f" • 🚀 Artillery: {army['artillery']}",
    ]

    await update.message.reply_text("\n".join(text), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('status', status)
