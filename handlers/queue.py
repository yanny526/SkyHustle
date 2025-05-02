# handlers/queue.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.time_utils import format_hhmmss
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /queue - list pending building upgrades, after ticking resources
    and notifying of any completed upgrades.
    """
    user = update.effective_user
    uid = str(user.id)
    now = time.time()

    # 1) Tick resources
    added = tick_resources(uid)

    # 2) Complete any finished upgrades
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(
            f"✅ {btype} upgrade complete! Now Lvl {lvl}."
            for btype, lvl in done
        )
        await update.message.reply_text(msgs)

    # 3) Fetch pending upgrades
    pending = []
    for row in get_rows('Buildings')[1:]:
        if row[0] != uid:
            continue
        lvl = int(row[2])
        if row[3]:
            end_ts = float(row[3])
            if end_ts > now:
                pending.append((row[1], lvl + 1, end_ts))

    # 4) Respond
    if not pending:
        return await update.message.reply_text("✅ You have no upgrades in progress.")

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
