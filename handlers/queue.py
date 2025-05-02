# handlers/queue.py

import time
from telegram import Update, ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /queue - list all pending building upgrades with remaining time.
    """
    user = update.effective_user
    uid = str(user.id)
    now = time.time()

    # Fetch building upgrade entries
    rows = get_rows('Buildings')[1:]  # skip header
    pending = []
    for row in rows:
        if row[0] != uid:
            continue
        btype = row[1]
        lvl = int(row[2])
        if len(row) > 3 and row[3]:
            end_ts = float(row[3])
            if end_ts > now:
                pending.append((btype, lvl + 1, end_ts))

    if not pending:
        await update.message.reply_text("✅ You have no upgrades in progress.")
        return

    # Build response
    lines = ["⏳ *Upgrades in Progress* ⏳\n"]
    emoji_map = {
        'Mine': '⛏️', 'Power Plant': '⚡',
        'Barracks': '🛡️', 'Workshop': '🔧'
    }
    for btype, next_lvl, end_ts in pending:
        rem = format_hhmmss(int(end_ts - now))
        emoji = emoji_map.get(btype, '')
        lines.append(f" • {emoji} {btype} → Lvl {next_lvl} ({rem} remaining)")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('queue', queue)
