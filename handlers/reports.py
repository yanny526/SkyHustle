# handlers/reports.py

from datetime import datetime, timezone
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from sheets_service import get_rows
from modules.unit_manager import UNITS
from utils.format_utils import code as md_code

PEND_SHEET = "PendingActions"

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports – display your pending missions with enhanced UI.
    """
    chat_id = str(update.effective_chat.id)
    now = datetime.now(timezone.utc)

    raw = get_rows(PEND_SHEET)[1:]
    ops = []
    for row in raw:
        job_name, code_str, uid, defender_id, defender_name, comp_json, scouts, run_at, typ, status = (
            row + [""] * 10
        )[:10]
        if uid != chat_id or status != "pending":
            continue

        # compute ETA
        try:
            run_dt = datetime.fromisoformat(run_at)
            secs = int((run_dt - now).total_seconds())
            if secs <= 0:
                continue
            m, s = divmod(secs, 60)
            eta = f"{m}m{s:02d}s"
        except Exception:
            secs, eta = float('inf'), "??"

        if typ == "scout":
            count = int(scouts) if scouts.isdigit() else scouts or 1
            ops.append({"type":"scout","defender":defender_name,"count":count,"eta":eta,"secs":secs,"code":code_str})
        else:
            try:
                comp = json.loads(comp_json) if comp_json else {}
            except Exception:
                comp = {}
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k, v in comp.items()) or "All troops"
            ops.append({"type":"attack","defender":defender_name,"comp":comp_str,"eta":eta,"secs":secs,"code":code_str})

    # sort by ETA
    ops.sort(key=lambda o: o.get("secs", float('inf')))

    total = len(ops)
    lines = []

    # Header
    lines.append("📜 ----- Pending Missions -----")
    lines.append("")
    if total == 0:
        lines.append("✅ You have no pending missions.")
        lines.append("")
        lines.append("Dispatch an operation with `/attack <Commander> ...`.")
    else:
        lines.append(f"🔥 {total} mission{'s' if total!=1 else ''} in progress")

        # Recon Section
        scouts = [o for o in ops if o['type']=='scout']
        if scouts:
            lines.append("")
            lines.append("🔎 ----- Recon Operations -----")
            for o in scouts:
                lines.append(f"• 👁️ *{o['defender']}* — Scouts×{o['count']} — ETA {o['eta']} — {md_code(o['code'])}")

        # Assault Section
        attacks = [o for o in ops if o['type']=='attack']
        if attacks:
            lines.append("")
            lines.append("🏹 ----- Assault Operations -----")
            for o in attacks:
                lines.append(f"• 💥 *{o['defender']}* — {o['comp']} — ETA {o['eta']} — {md_code(o['code'])}")

        lines.append("")
        lines.append("❗ Cancel with `/attack -c <code>`.")

    text = "\n".join(lines)

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

handler = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
