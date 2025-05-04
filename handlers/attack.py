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

# --- New DeployedArmy tab setup ---
DEP_SHEET   = "DeployedArmy"
DEP_HEADER  = ["uid","unit_key","count","job_name"]

def _ensure_deployed_sheet():
    rows = get_rows(DEP_SHEET)
    if not rows or rows[0] != DEP_HEADER:
        append_row(DEP_SHEET, DEP_HEADER)

# (PendingActions code remains as before) …
PEND_SHEET  = "PendingActions"
PEND_HEADER = ["job_name","uid","defender_id","defender_name",
               "composition","scout_count","run_time","type","status"]

def _ensure_pending_sheet():
    rows = get_rows(PEND_SHEET)
    if not rows or rows[0] != PEND_HEADER:
        append_row(PEND_SHEET, PEND_HEADER)

async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    # … unchanged …

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    data           = context.job.data
    chat_id        = int(data["uid"])
    defender_id    = data["defender_id"]
    defender_name  = data["defender_name"]
    attacker_name  = data["attacker_name"]
    atk_i, def_i   = data["atk_i"], data["def_i"]
    comp           = data["composition"]
    timestamp      = data["timestamp"]
    job_name       = context.job.name

    # … combat as before …

    # update sheets & log
    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog",[data["uid"],str(defender_id),timestamp,result,str(spoils)])

    # === New: return deployed troops ===
    _ensure_deployed_sheet()
    dep_rows = get_rows(DEP_SHEET)
    for idx, row in enumerate(dep_rows[1:], start=1):
        uid, key, cnt, jn = row
        if jn == job_name:
            survivors = int(cnt)
            # add back to Army
            army = get_rows("Army")
            for ai, arow in enumerate(army[1:], start=1):
                if arow[0]==uid and arow[1]==key:
                    arow[2] = str(int(arow[2]) + survivors)
                    update_row("Army", ai, arow)
                    break
            else:
                append_row("Army", [uid, key, str(survivors)])
            # clear deployed entry
            row[2] = "0"
            update_row(DEP_SHEET, idx, row)

    # send result
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

    # mark done in PendingActions (unchanged)…

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    uid     = str(user.id)
    args    = context.args.copy()
    chat_id = update.effective_chat.id

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <Commander> … [-u units] [-s scouts] [--scout-only]`",
            parse_mode=ParseMode.MARKDOWN
        )

    # parse flags as before…
    # … build `comp`, `scout_count`, `scout_only`

    # locate attacker/defender…

    # energy check…

    # === New: record deployed troops instead of raw deduction only ===
    _ensure_deployed_sheet()
    for key, qty in comp.items():
        if qty <= 0: continue
        # deduct from garrison:
        army = get_rows("Army")
        for i, row in enumerate(army[1:], start=1):
            if row[0]==uid and row[1]==key:
                new = max(0, int(row[2]) - qty)
                row[2] = str(new)
                update_row("Army", i, row)
                break
        # record deployment under this job:
        # (job_name not known yet – will append after scheduling)

    ts = str(int(time.time()))
    _ensure_pending_sheet()

    # schedule scouts & append both sheets
    if scout_count>0:
        name = f"scout_{uid}_{defender[0]}_{ts}"
        j = context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=name,
            data={"uid": uid,"defender_id":defender[0],"defender_name":defender[1]}
        )
        run_time = (datetime.utcnow()+timedelta(minutes=5)).replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [name, uid, defender[0], defender[1],
                                json.dumps(comp), str(scout_count),
                                run_time, "scout", "pending"])

    if not scout_only:
        name = f"attack_{uid}_{defender[0]}_{ts}"
        j = context.job_queue.run_once(
            combat_resolution_job,
            when=timedelta(minutes=30),
            name=name,
            data={
                "uid": uid, "defender_id": defender[0],
                "attacker_name": attacker[1],
                "defender_name": defender[1],
                "atk_i": atk_i, "def_i": def_i,
                "timestamp": ts, "composition": comp
            }
        )
        run_time = (datetime.utcnow()+timedelta(minutes=30)).replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [name, uid, defender[0], defender[1],
                                json.dumps(comp),"0", run_time,
                                "attack","pending"])
        # now record deployments & link to job_name
        for key, qty in comp.items():
            if qty <= 0: continue
            append_row(DEP_SHEET, [uid, key, str(qty), name])

    # challenges & UI confirmation…
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(confirmation_text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

handler = CommandHandler("attack", attack)
