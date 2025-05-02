# handlers/train.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train <unit> <count> - train units, tick resources, complete upgrades, deduct energy.
    """
    user = update.effective_user
    uid = str(user.id)

    # tick & upgrades
    tick_resources(uid)
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(f"✅ {b} upgrade done! Now Lvl {lvl}." for b,lvl in done)
        await update.message.reply_text(msgs)

    args = context.args
    if len(args)<2:
        return await update.message.reply_text(
            "❗ Usage: `/train <unit> <count>`\n"
            "Infantry(1⚡), Tanks(5⚡), Artillery(10⚡)",
            parse_mode=ParseMode.MARKDOWN
        )

    u = args[0].lower()
    unit_map = {'infantry':'infantry','tanks':'tanks','tank':'tanks','artillery':'artillery'}
    if u not in unit_map:
        return await update.message.reply_text(
            f"❌ Unknown unit *{args[0]}*.",
            parse_mode=ParseMode.MARKDOWN
        )
    unit = unit_map[u]
    try:
        cnt = int(args[1])
        if cnt<1: raise
    except:
        return await update.message.reply_text("❌ Count must be >0.")

    COSTS = {
        'infantry': {'c':10,'m':5,'e':1},
        'tanks':    {'c':100,'m':50,'e':5},
        'artillery':{'c':200,'m':100,'e':10},
    }
    cost = COSTS[unit]
    totC,totM,totE = cost['c']*cnt, cost['m']*cnt, cost['e']*cnt

    # fetch player row
    rows = get_rows('Players')
    for pi,row in enumerate(rows[1:],start=1):
        if row[0]==uid:
            prow,row_idx = row.copy(),pi
            break
    else:
        return await update.message.reply_text("❗ Run /start first.")

    creds,minr,engy = map(int,(prow[3],prow[4],prow[5]))
    if creds<totC or minr<totM or engy<totE:
        return await update.message.reply_text(
            f"❌ Need {totC}💳 {totM}⛏️ {totE}⚡."
        )

    # deduct
    prow[3]=str(creds-totC)
    prow[4]=str(minr-totM)
    prow[5]=str(engy-totE)
    update_row('Players',row_idx,prow)

    # update army
    army = get_rows('Army')
    found=None
    for ai,row in enumerate(army[1:],start=1):
        if row[0]==uid and row[1]==unit:
            found=(ai,row.copy()); break

    if found:
        ai,arow = found
        arow[2]=str(int(arow[2])+cnt)
        update_row('Army',ai,arow)
    else:
        append_row('Army',[uid,unit,str(cnt)])

    emoji = {'infantry':'👨‍✈️','tanks':'🛡️','artillery':'🚀'}[unit]
    await update.message.reply_text(
        f"{emoji} Trained {cnt}×{unit}! Spent {totC}💳 {totM}⛏️ {totE}⚡."
    )

handler = CommandHandler('train', train)
