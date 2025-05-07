# handlers/reports.py

from datetime import datetime, timezone
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from sheets_service import get_rows
from modules.unit_manager import UNITS
from utils.format_utils import section_header, code as md_code

PEND_SHEET = "PendingActions"

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports – list your pending scouts & attacks.
    """
    chat_id = str(update.effective_chat.id)
    now     = datetime.now(timezone.utc)

    # Collect pending operations
    ops = []
    for row in get_rows(PEND_SHEET)[1:]:
        # Ensure we have 10 columns, in correct order:
        # job_name, code, uid, defender_id, defender_name,
        # comp_json, scouts, run_at, typ, status
        job_name, code_str, uid, defender_id, defender_name, comp_json, scouts, run_at, typ, status = (
            row + [""] * 10
        )[:10]
        if uid != chat_id or status != "pending":
            continue

        # Parse ETA
        try:
            run_dt = datetime.fromisoformat(run_at)
        except Exception:
            continue
        delta = run_dt - now
        secs  = int(delta.total_seconds())
        if secs <= 0:
            continue
        m, s = divmod(secs, 60)

        if typ == "scout":
            ops.append(
                f"🔎 Scout on *{defender_name}* arriving in {m}m{s:02d}s  {md_code(code_str)}  (×{scouts})"
            )
        else:
            try:
                comp = json.loads(comp_json) if comp_json else {}
            except json.JSONDecodeError:
                comp = {}
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k, v in comp.items()) or "All troops"
            ops.append(
                f"🏹 Attack on *{defender_name}* ({comp_str}) arriving in {m}m{s:02d}s  {md_code(code_str)}"
            )

    # Build response
    if not ops:
        text = "\n".join([
            section_header("🗒️ Pending Operations"),
            "",
            "✅ You have no pending operations.",
            "",
            "Send an attack with `/attack <Commander> ...`"
        ])
    else:
        lines = [section_header("🗒️ Pending Operations"), ""]
        for line in ops:
            lines.append(f"• {line}")
        lines.extend([
            "",
            "❗ Cancel with `/attack -c <code>`"
        ])
        text = "\n".join(lines)

    # Inline refresh button
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        except BadRequest as e:
            # ignore if no changes
            if "Message is not modified" not in str(e):
                raise

async def reports_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await reports(update, context)

handler          = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
