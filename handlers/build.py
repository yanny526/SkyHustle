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
    'mine': ('Mine','⛏️'),
    'powerplant':('Power Plant','⚡'),
    'power plant':('Power Plant','⚡'),
    'barracks':('Barracks','🛡️'),
    'workshop':('Workshop','🔧'),
}

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    # pre‐tick & upgrades
    tick_resources(uid)
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(f"✅ {b} upgrade done! Now Lvl {lvl}." for b,lvl in done)
        await update.message.reply_text(msgs)

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

    # fetch player
    players = get_rows('Players')
    for pi,row in enumerate(players[1:],start=1):
        if row[0]==uid:
            prow,row_idx = row.copy(),pi
            break
    else:
        return await update.message.reply_text("❗ Run /start first.")

    # resources
    credits,minerals,energy = map(int,(prow[3],prow[4],prow[5]))

    # current level
    buildings = get_rows('Buildings')
    cur_lvl=0; existing=None
    for bi,row in enumerate(buildings[1:],start=1):
        if row[0]==uid and row[1]==btype:
            cur_lvl=int(row[2]); existing=(bi,row.copy()); break

    L=cur_lvl+1
    # cost & time
    if btype=='Mine':
        cC, cM, sec = 100, 50*L, 30*60*L
        eC = 10*L
    elif btype=='Power Plant':
        cC, cM, sec = 100, 30*L, 20*60*L
        eC = 8*L
    elif btype=='Barracks':
        cC, cM, sec = 150,70*L,45*60*L
        eC = 12*L
    else:
        cC, cM, sec = 200,100*L,60*60*L
        eC = 15*L

    if credits<cC or minerals<cM or energy<eC:
        return await update.message.reply_text(
            f"❌ Need {cC}💳, {cM}⛏️, {eC}⚡.",
            parse_mode=ParseMode.MARKDOWN
        )

    # deduct
    prow[3]=str(credits-cC)
    prow[4]=str(minerals-cM)
    prow[5]=str(energy-eC)
    update_row('Players',row_idx,prow)

    # schedule
    end_ts = now+sec
    if existing:
        bi,brow = existing
        brow[3]=str(end_ts)
        update_row('Buildings',bi,brow)
    else:
        append_row('Buildings',[uid,btype,str(cur_lvl),str(end_ts)])

    await update.message.reply_text(
        f"🔨 Upgrading {emoji} *{btype}* → Lvl {L}\n"
        f"Cost: {cC}💳 {cM}⛏️ {eC}⚡ | {format_hhmmss(sec)}",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler('build', build)
