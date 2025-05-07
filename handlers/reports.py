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
    /reports – display your pending missions (outgoing & incoming) with enhanced UI.
    """
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

        # determine role
        if uid == chat_id:
            role = "outgoing"
        elif defender_id == chat_id:
            role = "incoming"
        else:
            continue

        entry = {"type": typ, "role": role, "eta": eta, "secs": secs, "code": code_str}

        if typ == "scout":
            entry["count"] = int(scouts) if scouts.isdigit() else 1
        else:
            try:
                comp = json.loads(comp_json) if comp_json else {}
            except Exception:
                comp = {}
            entry["comp"] = " ".join(f"{UNITS[k][1]}×{v}" for k, v in comp.items()) or "All troops"

        # actor name (for incoming)
        if role == "incoming":
            parts = job_name.split("_")
            attacker_id = parts[1] if len(parts) > 1 else None
            entry["actor"] = players.get(attacker_id, "Unknown")
        else:
            entry["actor"] = defender_name

        ops.append(entry)

    # sort by ETA
    ops.sort(key=lambda o: o.get("secs", float('inf')))
    total = len(ops)

    lines = []
    lines.append("📜 ----- Pending Missions -----")
    lines.append("")

    if total == 0:
        lines.extend([
            "✅ You have no pending missions.",
            "",
            "Dispatch an operation with `/attack <Commander> ...`."
        ])
    else:
        lines.append(f"🔥 {total} mission{'s' if total!=1 else ''} in progress")

        # Recon section
        recon_ops = [o for o in ops if o['type']=='scout']
        if recon_ops:
            lines.append("")
            lines.append("🔎 ----- Recon Operations -----")
            for o in recon_ops:
                if o['role']=='outgoing':
                    lines.append(
                        f"• 👁️ Scout on *{o['actor']}* — {o['count']} units — ETA {o['eta']} — {md_code(o['code'])}"
                    )
                else:
                    lines.append(
                        f"• 🔔 Incoming scouts from *{o['actor']}* — {o['count']} units — ETA {o['eta']} — {md_code(o['code'])}"
                    )

        # Assault section
        attack_ops = [o for o in ops if o['type']=='attack']
        if attack_ops:
            lines.append("")
            lines.append("🏹 ----- Assault Operations -----")
            for o in attack_ops:
                if o['role']=='outgoing':
                    lines.append(
                        f"• 💥 Attack on *{o['actor']}* — {o['comp']} — ETA {o['eta']} — {md_code(o['code'])}"
                    )
                else:
                    lines.append(
                        f"• 🚨 Incoming attack by *{o['actor']}* — {o['comp']} — ETA {o['eta']} — {md_code(o['code'])}"
                    )

        lines.append("")
        lines.append("❗ Cancel with `/attack -c <code>`. ")

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
