from datetime import datetime, timezone
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from modules.unit_manager import UNITS

PEND_SHEET = "PendingActions"

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    now     = datetime.now(timezone.utc)

    lines = []
    for row in get_rows(PEND_SHEET)[1:]:
        job, uid, did, dname, comp_json, scouts, run_at, typ, status = row
        if status!="pending" or uid!=chat_id:
            continue

        run_dt = datetime.fromisoformat(run_at)
        delta  = run_dt - now
        mins, secs = divmod(int(delta.total_seconds()), 60)

        if typ=="scout":
            lines.append(f"🔎 Scouts on *{dname}* in {mins}m {secs}s (×{scouts})")
        else:  # attack
            comp = json.loads(comp_json)
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k,v in comp.items())
            lines.append(f"🏹 Attack on *{dname}* [{comp_str}] in {mins}m {secs}s")

    text = "🗒️ *No pending operations.*" if not lines else "🗒️ *Pending Operations:*\n" + "\n".join(lines)
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

async def reports_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await reports(update, context)

handler          = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
