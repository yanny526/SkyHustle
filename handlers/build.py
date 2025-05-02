# handlers/build.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, append_row, update_row
from utils.time_utils import format_hhmmss
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

# map input → (sheet name, emoji)
BUILDINGS = {
    'mine': ('Mine', '⛏️'),
    'powerplant': ('Power Plant', '⚡'),
    'power plant': ('Power Plant', '⚡'),
    'barracks': ('Barracks', '🛡️'),
    'workshop': ('Workshop', '🔧'),
}

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    # 1) Tick resources + complete upgrades
    tick_resources(uid)
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(f"✅ {b} upgrade complete! Now Lvl {lvl}."
                         for b, lvl in done)
        await update.message.reply_text(msgs)

    # 2) Parse args
    args = context.args
    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/build <building>`\n"
            "Valid: mine, powerplant, barracks, workshop",
            parse_mode=ParseMode.MARKDOWN
        )

    key = args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"❌ Unknown building *{args[0]}*.",
            parse_mode=ParseMode.MARKDOWN
        )
    btype, emoji = BUILDINGS[key]
    now = time.time()

    # 3) Fetch player row
    players = get_rows('Players')
    for pi, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            prow, prow_idx = row.copy(), pi
            break
    else:
        return await update.message.reply_text("❗ Run /start first.")

    credits, minerals, energy = map(int, (prow[3], prow[4], prow[5]))

    # 4) Fetch building row (if exists)
    buildings = get_rows('Buildings')
    cur_lvl = 0
    existing = None
    for bi, row in enumerate(buildings[1:], start=1):
        if row[0] == uid and row[1] == btype:
            cur_lvl = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
            existing = (bi, row.copy())
            break

    L = cur_lvl + 1
    # 5) Compute cost & duration & energy cost
    if btype == 'Mine':
        cC, cM, sec, eC = 100, 50 * L, 30 * 60 * L, 10 * L
    elif btype == 'Power Plant':
        cC, cM, sec, eC = 100, 30 * L, 20 * 60 * L, 8 * L
    elif btype == 'Barracks':
        cC, cM, sec, eC = 150, 70 * L, 45 * 60 * L, 12 * L
    else:  # Workshop
        cC, cM, sec, eC = 200, 100 * L, 60 * 60 * L, 15 * L

    if credits < cC or minerals < cM or energy < eC:
        return await update.message.reply_text(
            f"❌ Need {cC}💳, {cM}⛏️, {eC}⚡.",
            parse_mode=ParseMode.MARKDOWN
        )

    # 6) Deduct resources
    prow[3] = str(credits - cC)
    prow[4] = str(minerals - cM)
    prow[5] = str(energy - eC)
    update_row('Players', prow_idx, prow)

    # 7) Schedule upgrade (ensure at least 4 columns)
    end_ts = now + sec
    if existing:
        bi, brow = existing
        # make sure brow has index 3
        while len(brow) < 4:
            brow.append('')
        brow[3] = str(end_ts)
        update_row('Buildings', bi, brow)
    else:
        append_row('Buildings', [uid, btype, str(cur_lvl), str(end_ts)])

    # 8) Confirmation message
    await update.message.reply_text(
        f"🔨 Upgrading {emoji} *{btype}* → Lvl {L}\n"
        f"Cost: {cC}💳 {cM}⛏️ {eC}⚡ | {format_hhmmss(sec)}",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler('build', build)
