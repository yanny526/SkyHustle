# handlers/queue.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss
from utils.decorators import game_command

@game_command
async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /queue - list pending upgrades (tick & upgrades via decorator).
    """
    user = update.effective_user
    uid = str(user.id)
    now = time.time()

    pending = []
    for row in get_rows('Buildings')[1:]:
        if row[0] != uid:
            continue
        lvl = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
        if len(row) > 3 and row[3]:
            try:
                end_ts = float(row[3])
                if end_ts > now:
                    pending.append((row[1], lvl + 1, end_ts))
            except ValueError:
                continue

    if not pending:
        text = "✅ You have no upgrades in progress."
    else:
        lines = ["⏳ *Upgrades in Progress* ⏳\n"]
        emoji_map = {
            'Mine': '⛏️', 'Power Plant': '⚡',
            'Barracks': '🛡️', 'Workshop': '🔧'
        }
        for btype, next_lvl, end_ts in pending:
            rem = format_hhmmss(int(end_ts - now))
            emoji = emoji_map.get(btype, '')
            lines.append(f" • {emoji} {btype} → Lvl {next_lvl} ({rem} remaining)")
        text = "\n".join(lines)

    # ✅ Support both message and callback trigger
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('queue', queue)
