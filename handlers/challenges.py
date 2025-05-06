# handlers/queue.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss
from utils.decorators import game_command
from utils.format_utils import (
    format_bar,
    get_building_emoji,
    get_build_time,
    section_header,
)

@game_command
async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /queue – list pending upgrades with progress bars.
    """
    uid = str(update.effective_user.id)
    now = time.time()

    # Gather pending builds
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

    # No pending builds
    if not pending:
        text = "\n".join([
            section_header("🔧 Upgrade Queue", pad_char="=", pad_count=3),
            "",
            "✅ You have no upgrades in progress.",
            "",
            "Start one with `/build <building>`!"
        ])
        return await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # Build the queue UI
    lines = [section_header("⏳ Upgrades In Progress", pad_char="=", pad_count=3), ""]
    for btype, next_lvl, end_ts in pending:
        total_sec = get_build_time(btype, next_lvl)
        remaining = int(end_ts - now)
        elapsed   = max(0, min(total_sec - remaining, total_sec))
        bar       = format_bar(elapsed, total_sec)
        emoji     = get_building_emoji(btype)
        lines.append(
            f"{emoji} *{btype}* → Lvl {next_lvl}\n"
            f"{bar} ({format_hhmmss(remaining)} left)"
        )
        lines.append("")  # blank line between entries

    text = "\n".join(lines).rstrip()
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('queue', queue)
