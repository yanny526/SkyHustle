# handlers/reports.py

import time
import logging
from datetime import datetime, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from sheets_service import get_rows, update_row

from utils.time_utils import format_hhmmss

logger = logging.getLogger(__name__)

# Sheet & header cols in PendingActions:
# 0 job_name, 1 code, 2 uid, 3 defender_id, 4 defender_name,
# 5 composition, 6 scout_count, 7 run_time, 8 type, 9 status
PEND_SHEET = "PendingActions"

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    rows = get_rows(PEND_SHEET)
    if not rows or len(rows) < 2:
        return await update.message.reply_text("📭 You have no pending operations.")

    header, *data = rows
    now = time.time()

    lines = ["📜 *Pending Operations*", ""]
    buttons = []

    for row in data:
        if len(row) < 10:
            continue
        job_name, code, puid, _, defender_name, _, _, run_ts_str, typ, status = row

        # only your pending jobs
        if puid != uid or status.lower() != "pending":
            continue

        # parse remaining time
        rem = ""
        try:
            # run_ts_str is ISO like "2025-05-15T14:30:00"
            end_dt = datetime.fromisoformat(run_ts_str)
            end_ts = end_dt.replace(tzinfo=timezone.utc).timestamp()
            secs_left = max(0, int(end_ts - now))
            rem = format_hhmmss(secs_left)
        except Exception as e:
            logger.debug("Couldn't parse run_time %r: %s", run_ts_str, e)
            rem = run_ts_str

        # build line and a “cancel” button
        label = "🔎 Scout" if typ == "scout" else "🏹 Attack"
        lines.append(f"• {label} → {defender_name} in {rem} – Code: `{code}`")
        buttons.append([
            InlineKeyboardButton(
                f"❌ Cancel {label.split()[1]} {code}",
                callback_data=f"reports_cancel:{code}"
            )
        ])

    if len(lines) == 2:
        # we added only header + blank
        await update.message.reply_text("📭 You have no pending operations.", parse_mode=ParseMode.MARKDOWN)
    else:
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("\n".join(lines),
                                        parse_mode=ParseMode.MARKDOWN,
                                        reply_markup=markup)

async def reports_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline-button “Cancel CODE” in the pending list."""
    q = update.callback_query
    await q.answer()
    _, code = q.data.split(":", 1)

    rows = get_rows(PEND_SHEET)
    header, *data = rows
    for idx, row in enumerate(data, start=1):
        if len(row) >= 10 and row[1] == code and row[9].lower() == "pending":
            # mark cancelled
            row[9] = "cancelled"
            update_row(PEND_SHEET, idx, row)
            # notify
            await q.edit_message_text(f"🚫 Operation `{code}` cancelled.", parse_mode=ParseMode.MARKDOWN)
            return

    await q.answer(text="❗ Couldn't find that pending operation.", show_alert=True)

handler       = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_cancel, pattern=r"^reports_cancel:")
