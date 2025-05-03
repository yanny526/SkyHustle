import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, append_row, update_row
from utils.time_utils import format_hhmmss
from utils.decorators import game_command
from config import BUILDING_MAX_LEVEL

BUILDINGS = {
    'mine': ('Mine', '⛏️'),
    'powerplant': ('Power Plant', '⚡'),
    'power plant': ('Power Plant', '⚡'),
    'barracks': ('Barracks', '🛡️'),
    'workshop': ('Workshop', '🔧'),
}

@game_command
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build <building> - start an upgrade (tick & upgrades via decorator).
    """
    user = update.effective_user
    uid = str(user.id)
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

    # 1) Fetch current level
    current_lvl = 0
    buildings = get_rows('Buildings')
    for row in buildings[1:]:
        if row[0] == uid and row[1] == btype:
            try:
                current_lvl = int(row[2])
            except:
                current_lvl = 0
            break

    # 2) Check cap
    max_lvl = BUILDING_MAX_LEVEL.get(btype)
    if max_lvl is not None and current_lvl >= max_lvl:
        return await update.message.reply_text(
            f"🏆 *{btype}* is already max Level {max_lvl}!",
            parse_mode=ParseMode.MARKDOWN
        )

    # 3) Compute next level & costs
    L = current_lvl + 1
    now = time.time()
    if btype == 'Mine':
        cC, cM, sec, eC = 100, 50 * L, 30 * 60 * L, 10 * L
    elif btype == 'Power Plant':
        cC, cM, sec, eC = 100, 30 * L, 20 * 60 * L, 8 * L
    elif btype == 'Barracks':
        cC, cM, sec, eC = 150, 70 * L, 45 * 60 * L, 12 * L
    else:  # Workshop
        cC, cM, sec, eC = 200, 100 * L, 60 * 60 * L, 15 * L

    # 4) Fetch & check resources
    players = get_rows('Players')
    for pi, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            prow, prow_idx = row.copy(), pi
            break
    else:
        return await update.message.reply_text("❗ Run /start first.")

    credits, minerals, energy = map(int, (prow[3], prow[4], prow[5]))
    if credits < cC or minerals < cM or energy < eC:
        return await update.message.reply_text(
            f"❌ Need {cC}💳 {cM}⛏️ {eC}⚡.",
            parse_mode=ParseMode.MARKDOWN
        )

    # 5) Deduct & schedule
    prow[3], prow[4], prow[5] = str(credits - cC), str(minerals - cM), str(energy - eC)
    update_row('Players', prow_idx, prow)

    end_ts = now + sec
    # preserve existing building row or append new
    existing = None
    for bi, brow in enumerate(buildings[1:], start=1):
        if brow[0] == uid and brow[1] == btype:
            existing = (bi, brow.copy())
            break

    if existing:
        bi, brow_copy = existing
        while len(brow_copy) < 4:
            brow_copy.append('')
        brow_copy[3] = str(end_ts)
        update_row('Buildings', bi, brow_copy)
    else:
        append_row('Buildings', [uid, btype, str(current_lvl), str(end_ts)])

    # 6) Confirmation
    confirm_text = (
        f"🔨 Upgrading {emoji} *{btype}* → Lvl {L}\n"
        f"Cost: {cC}💳 {cM}⛏️ {eC}⚡ | {format_hhmmss(sec)}"
    )
    await update.message.reply_text(confirm_text, parse_mode=ParseMode.MARKDOWN)

    # 7) QUEST PROGRESSION STEP 2: Upgrade Power Plant
    if btype == "Power Plant":
        # step2 reward
        header = players[0]
        while len(prow) < len(header):
            prow.append("")
        if prow[7] != "step2":
            prow[7] = "step2"
            prow[4] = str(int(prow[4]) + 100)  # +100 minerals
            update_row('Players', prow_idx, prow)
            await update.message.reply_text(
                "🎉 Mission Update!\n"
                "✅ You’ve upgraded your Power Plant!\n"
                "💎 +100 bonus Minerals!\n\n"
                "Now try training your first unit:\n"
                "`/train infantry 5`",
                parse_mode=ParseMode.MARKDOWN
            )

        # ← NEW: track weekly challenge
        from modules.challenge_manager import load_challenges, update_player_progress
        for ch in load_challenges('weekly'):
            if ch.key == 'powerplant_upgrades':
                update_player_progress(uid, ch)
                break

handler = CommandHandler('build', build)
