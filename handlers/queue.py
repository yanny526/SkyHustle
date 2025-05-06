import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss
from utils.decorators import game_command
from utils.format_utils import format_bar, get_building_emoji

@game_command
async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /queue - list pending upgrades (tick & upgrades via decorator) with progress bars.
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
        for btype, next_lvl, end_ts in pending:
            # remaining and total duration
            remaining = int(end_ts - now)
            # Recompute total time based on building type & target level:
            if btype == 'Mine':
                total_sec = 30 * 60 * next_lvl
            elif btype == 'Power Plant':
                total_sec = 20 * 60 * next_lvl
            elif btype == 'Barracks':
                total_sec = 45 * 60 * next_lvl
            else:  # Workshop
                total_sec = 60 * 60 * next_lvl

            elapsed = total_sec - remaining
            # clamp
            elapsed = max(0, min(elapsed, total_sec))

            bar = format_bar(elapsed, total_sec)
            emoji = get_building_emoji(btype)
            lines.append(
                f" • {emoji} {btype} → Lvl {next_lvl} {bar} ({format_hhmmss(remaining)} left)"
            )

        text = "\n".join(lines)

    # Send or edit
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('queue', queue)
