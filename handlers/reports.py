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
    /reports – list your pending scouts & assaults in a captivating UI.
    """
    chat_id = str(update.effective_chat.id)
    now = datetime.now(timezone.utc)

    rows = get_rows(PEND_SHEET)[1:]
    ops = []
    for row in rows:
        job_name, code_str, uid, defender_id, defender_name, comp_json, scouts, run_at, typ, status = (
            row + [""] * 10
        )[:10]
        if uid != chat_id or status != "pending":
            continue
        # compute ETA
        try:
            run_dt = datetime.fromisoformat(run_at)
            delta = run_dt - now
            secs = int(delta.total_seconds())
            if secs <= 0:
                continue
            m, s = divmod(secs, 60)
            eta = f"{m}m{s:02d}s"
        except Exception:
            secs, eta = float('inf'), "unknown"

        if typ == "scout":
            count = int(scouts) if scouts.isdigit() else scouts or "1"
            ops.append({
                "type": "scout",
                "defender_name": defender_name,
                "count": count,
                "eta": eta,
                "secs": secs,
                "code": code_str
            })
        else:
            try:
                comp = json.loads(comp_json) if comp_json else {}
            except json.JSONDecodeError:
                comp = {}
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k, v in comp.items()) or "All troops"
            ops.append({
                "type": "attack",
                "defender_name": defender_name,
                "comp_str": comp_str,
                "eta": eta,
                "secs": secs,
                "code": code_str
            })
    # sort by soonest
    ops.sort(key=lambda o: o["secs"])

    total = len(ops)
    if total == 0:
        text_lines = [
            section_header("🗒️ Pending Missions"),
            "",
            "✅ You have no pending missions.",
            "",
            "Dispatch an operation with `/attack <Commander> ...`"
        ]
    else:
        text_lines = [
            section_header("🗒️ Pending Missions"),
            f"🔥 *{total}* mission{'s' if total!=1 else ''} in progress", ""
        ]
        # Recon
        scouts = [o for o in ops if o["type"] == "scout"]
        if scouts:
            text_lines += [section_header("🔎 Recon Operations"), ""]
            for o in scouts:
                text_lines.append(
                    f"• 👁️ *{o['defender_name']}* — Scouts: {o['count']} — ETA {o['eta']} — {md_code(o['code'])}"
                )
            text_lines.append("")
        # Assault
        attacks = [o for o in ops if o["type"] == "attack"]
        if attacks:
            text_lines += [section_header("🏹 Assault Operations"), ""]
            for o in attacks:
                text_lines.append(
                    f"• 💥 *{o['defender_name']}* — {o['comp_str']} — ETA {o['eta']} — {md_code(o['code'])}"
                )
        text_lines.extend(["", "❗ Cancel with `/attack -c <code>`"])

    text = "\n".join(text_lines)
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )
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

handler = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
