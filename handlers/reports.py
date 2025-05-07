# handlers/reports.py

from datetime import datetime, timezone
import json
from math import ceil

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from sheets_service import get_rows
from modules.unit_manager import UNITS
from utils.format_utils import code as md_code

PEND_SHEET = "PendingActions"
PAGE_SIZE = 5

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports [page] – display your pending missions with pagination.
    """
    # Determine page number
    page = 1
    if update.message:
        args = context.args or []
        if args and args[0].isdigit():
            page = max(1, int(args[0]))
    else:
        # callback query data: "reports" or "reports_<page>"
        data = update.callback_query.data or ""
        parts = data.split("_")
        if len(parts) == 2 and parts[1].isdigit():
            page = max(1, int(parts[1]))

    chat_id = str(update.effective_chat.id)
    now = datetime.now(timezone.utc)

    raw = get_rows(PEND_SHEET)[1:]
    ops = []
    players = {r[0]: r[1] for r in get_rows("Players")[1:]}

    for row in raw:
        job_name, code_str, uid, defender_id, defender_name, comp_json, scouts, run_at, typ, status = (
            row + [""] * 10
        )[:10]
        if status != "pending":
            continue
        # parse ETA
        try:
            run_dt = datetime.fromisoformat(run_at)
            secs = int((run_dt - now).total_seconds())
            if secs <= 0:
                continue
            m, s = divmod(secs, 60)
            eta = f"{m}m{s:02d}s"
        except Exception:
            secs, eta = float('inf'), "??"

        # outgoing or incoming
        if uid == chat_id:
            role = 'outgoing'
            actor = defender_name
        elif defender_id == chat_id:
            role = 'incoming'
            parts = job_name.split("_")
            attacker_id = parts[1] if len(parts) > 1 else None
            actor = players.get(attacker_id, 'Unknown')
        else:
            continue

        # build entry
        entry = { 'type': typ, 'role': role, 'actor': actor, 'eta': eta, 'secs': secs, 'code': code_str }
        if typ == 'scout':
            entry['count'] = int(scouts) if scouts.isdigit() else 1
        else:
            try:
                comp = json.loads(comp_json) if comp_json else {}
            except Exception:
                comp = {}
            entry['comp'] = ' '.join(f"{UNITS[k][1]}×{v}" for k,v in comp.items()) or 'All troops'
        ops.append(entry)

    # sort by soonest
    ops.sort(key=lambda o: o['secs'])
    total = len(ops)
    total_pages = max(1, ceil(total / PAGE_SIZE))
    page = min(page, total_pages)

    # slice for current page
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_ops = ops[start:end]

    lines = []
    # header
    lines.append(f"📜 ----- Pending Missions (Page {page}/{total_pages}) -----")
    lines.append("")

    if total == 0:
        lines.extend([
            "✅ You have no pending missions.",
            "",
            "Dispatch an operation with `/attack <Commander> ...`"
        ])
    else:
        for o in page_ops:
            if o['type'] == 'scout':
                if o['role'] == 'outgoing':
                    lines.append(f"• 👁️ Scout on *{o['actor']}* — {o['count']} units — ETA {o['eta']} — {md_code(o['code'])}")
                else:
                    lines.append(f"• 🔔 Incoming scouts from *{o['actor']}* — {o['count']} units — ETA {o['eta']} — {md_code(o['code'])}")
            else:
                if o['role'] == 'outgoing':
                    lines.append(f"• 💥 Attack on *{o['actor']}* — {o['comp']} — ETA {o['eta']} — {md_code(o['code'])}")
                else:
                    lines.append(f"• 🚨 Incoming attack by *{o['actor']}* — {o['comp']} — ETA {o['eta']} — {md_code(o['code'])}")
        lines.append("")
        lines.append("❗ Cancel with `/attack -c <code>`.")

    text = "\n".join(lines)

    # build pagination buttons
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"reports_{page-1}"))
    buttons.append(InlineKeyboardButton("🔄 Refresh", callback_data=f"reports_{page}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"reports_{page+1}"))
    kb = InlineKeyboardMarkup([buttons])

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
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports(_\d+)?$")
