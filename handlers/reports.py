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
    chat_id = str(update.effective_chat.id)
    now     = datetime.now(timezone.utc)

    rows = get_rows(PEND_SHEET)[1:]
    lines = []
    buttons = []

    for job_name, code, uid, did, dname, comp_json, scouts, run_at, typ, status in rows:
        if status != "pending" or uid != chat_id:
            continue

        # time left
        run_dt = datetime.fromisoformat(run_at)
        delta  = run_dt - now
        mins, secs = divmod(int(delta.total_seconds()), 60)

        if typ == "scout":
            lines.append(f"🔎 Scouts ×{scouts} → *{dname}* in {mins}m {secs}s  (`{code}`)")
        else:
            comp = json.loads(comp_json)
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k,v in comp.items())
            lines.append(f"🏹 Attack {comp_str} → *{dname}* in {mins}m {secs}s  (`{code}`)")

        # add a cancel button for this code
        buttons.append(InlineKeyboardButton(f"❌ Cancel {code}", callback_data=f"cancel_{code}"))

    # build the message
    if not lines:
        text = "🗒️ *No pending operations.*"
        kb = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("🔄 Refresh", callback_data="reports")
        )
    else:
        text = "🗒️ *Pending Operations:*\n\n" + "\n\n".join(lines)
        # arrange cancel buttons two per row, then a final refresh button
        btn_rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        btn_rows.append([InlineKeyboardButton("🔄 Refresh", callback_data="reports")])
        kb = InlineKeyboardMarkup(btn_rows)

    # send or edit
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
    data = update.callback_query.data
    # Refresh
    if data == "reports":
        return await reports(update, context)
    # Cancel
    if data.startswith("cancel_"):
        code = data.split("_", 1)[1]
        # Reuse your attack handler with the `-c` flag
        update.message = update.callback_query.message
        update.message.text = f"/attack -c {code}"
        # directly invoke the attack handler
        from handlers.attack import attack as attack_cmd
        return await attack_cmd(update, context)

handler          = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^(reports|cancel_.*)$")
