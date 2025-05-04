# handlers/reports.py

from datetime import datetime, timezone
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from sheets_service import get_rows
from modules.unit_manager import UNITS

PEND_SHEET = "PendingActions"

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports – list your pending scouts & attacks (or show a friendly no-pending message).
    """
    chat_id = str(update.effective_chat.id)
    now     = datetime.now(timezone.utc)

    lines = []
    for row in get_rows(PEND_SHEET)[1:]:
        # only take the first 9 columns, ignore any extras
        job_name   = row[0]
        uid        = row[1]
        did        = row[2]
        dname      = row[3]
        comp_json  = row[4]
        scouts     = row[5]
        run_at     = row[6]
        typ        = row[7]
        status     = row[8]

        if status != "pending" or uid != chat_id:
            continue

        run_dt = datetime.fromisoformat(run_at)
        delta  = run_dt - now
        secs   = int(delta.total_seconds())
        if secs < 0:
            continue
        mins, secs = divmod(secs, 60)

        if typ == "scout":
            lines.append(f"🔎 Scouts on *{dname}* arriving in {mins}m{secs:02d}s (×{scouts})")
        else:
            comp = json.loads(comp_json) if comp_json else {}
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k,v in comp.items()) or "All troops"
            lines.append(f"🏹 Attack on *{dname}* [{comp_str}] arriving in {mins}m{secs:02d}s")

    if not lines:
        text = "🗒️ *No pending operations.*"
    else:
        text = "🗒️ *Pending Operations:*\n" + "\n".join(lines)

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

async def reports_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await reports(update, context)

handler          = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
