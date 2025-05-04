# handlers/attack.py

import time
import random
import json
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from modules.unit_manager import UNITS
from modules.challenge_manager import load_challenges, update_player_progress

PEND_SHEET  = "PendingActions"
PEND_HEADER = [
    "job_name", "code", "uid", "defender_id", "defender_name", 
    "composition", "scout_count", "run_time", "type", "status"
]

def _ensure_pending_sheet():
    rows = get_rows(PEND_SHEET)
    if not rows or rows[0] != PEND_HEADER:
        append_row(PEND_SHEET, PEND_HEADER)

def _generate_code() -> str:
    existing = {row[1] for row in get_rows(PEND_SHEET)[1:]}
    while True:
        code = f"{random.randint(0,99):02d}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
        if code not in existing:
            return code

async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    data          = context.job.data
    chat_id       = int(data["uid"])
    defender_name = data["defender_name"]
    job_name      = context.job.name

    # build scouting report (omitted for brevity)...

    # mark done
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[9] = "done"
            update_row(PEND_SHEET, idx, row)
            break

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    data      = context.job.data
    chat_id   = int(data["uid"])
    comp      = data["composition"]
    job_name  = context.job.name

    # resolve combat (omitted for brevity)...

    # mark done
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[9] = "done"
            update_row(PEND_SHEET, idx, row)
            break

async def return_troops_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    uid  = data["uid"]
    comp = data["composition"]
    chat_id = int(uid)

    # return troops
    army = get_rows("Army")
    for key, qty in comp.items():
        # find existing row
        for idx, r in enumerate(army[1:], start=1):
            if r[0] == uid and r[1] == key:
                r[2] = str(int(r[2]) + qty)
                update_row("Army", idx, r)
                break
        else:
            append_row("Army", [uid, key, str(qty)])

    # notify user
    parts = "\n".join(f"• {UNITS[k][1]}×{v}" for k, v in comp.items())
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🏠 *Troops Returned!*\n{parts}",
        parse_mode=ParseMode.MARKDOWN
    )

    # mark returned
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == context.job.name:
            row[9] = "returned"
            update_row(PEND_SHEET, idx, row)
            break

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only] [-c <CODE>]
    """
    args = context.args.copy()
    uid  = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    _ensure_pending_sheet()

    # --- CANCELLATION FLOW ---
    if "-c" in args:
        i = args.index("-c")
        if i+1 < len(args):
            code = args[i+1]
            # find matching pending attack
            rows = get_rows(PEND_SHEET)
            for idx, row in enumerate(rows[1:], start=1):
                if row[1] == code and row[2] == uid and row[8] == "attack" and row[9] == "pending":
                    job_name = row[0]
                    # cancel job
                    jobs = context.job_queue.get_jobs_by_name(job_name)
                    for job in jobs:
                        job.schedule_removal()
                    # mark cancelled
                    row[9] = "cancelled"
                    update_row(PEND_SHEET, idx, row)
                    # schedule return with same remaining time
                    # compute remaining
                    now = datetime.utcnow().replace(tzinfo=timezone.utc)
                    next_rt = jobs[0].next_run_time
                    delta = next_rt - now
                    # parse stored composition
                    comp = json.loads(row[5])
                    return_job = context.job_queue.run_once(
                        return_troops_job,
                        when=delta,
                        name=f"return_{job_name}",
                        data={"uid": uid, "composition": comp}
                    )
                    append_row(PEND_SHEET, [
                        return_job.name,  # job_name
                        code,            # same code
                        uid,
                        row[3],          # defender_id
                        row[4],          # defender_name
                        json.dumps(comp),
                        (now + delta).isoformat(),
                        "return",
                        "pending"
                    ])
                    return await update.message.reply_text(
                        f"✅ Cancelled attack {code}. Your troops are returning!",
                        parse_mode=ParseMode.MARKDOWN
                    )
        return await update.message.reply_text(
            "❌ Invalid or unknown cancel code.",
            parse_mode=ParseMode.MARKDOWN
        )

    # --- NORMAL ATTACK FLOW ---
    # parse flags & target...
    # (your existing scout-only / scout_count / comp parsing here)

    # after validating and deducting energy / troops...
    ts   = str(int(time.time()))
    code = _generate_code()

    # schedule scouts
    if scout_count > 0:
        j = context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=f"scout_{uid}_{target_id}_{ts}_{code}",
            data={"uid": uid, "defender_id": target_id, "defender_name": target_name}
        )
        run_time = (datetime.utcnow() + timedelta(minutes=5)).replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            j.name, code, uid, target_id, target_name,
            json.dumps(comp), str(scout_count),
            run_time, "scout", "pending"
        ])

    # schedule main attack
    if not scout_only:
        j = context.job_queue.run_once(
            combat_resolution_job,
            when=timedelta(minutes=30),
            name=f"attack_{uid}_{target_id}_{ts}_{code}",
            data={
                "uid": uid, "defender_id": target_id,
                "attacker_name": attacker_name, "defender_name": target_name,
                "atk_i": atk_i, "def_i": def_i,
                "timestamp": ts, "composition": comp
            }
        )
        run_time = (datetime.utcnow() + timedelta(minutes=30)).replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            j.name, code, uid, target_id, target_name,
            json.dumps(comp), "0",
            run_time, "attack", "pending"
        ])

    # track challenges...
    # UI confirmation...
    parts = [f"{UNITS[k][1]}×{v}" for k, v in comp.items()]
    if scout_count:
        parts.append(f"🔎 Scouts×{scout_count}")
    display = "\n".join([
        "⚔️ *Orders received!*",
        f"Target: *{target_name}*",
        *(["• 🔎 Scouts arriving in 5m"] if scout_count else []),
        *(["• 🏹 Attack arriving in 30m"] if not scout_only else []),
        f"\n• Code: `{code}`  — use `-c {code}` to cancel",
        *(["\n• " + "  ".join(parts)] if parts else [])
    ])
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(display, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

handler = CommandHandler("attack", attack)
