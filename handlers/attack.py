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

# where we track troops in flight
DEPLOY_SHEET  = "DeployedArmy"
DEPLOY_HEADER = ["job_name","uid","unit_key","quantity"]

# where we track pending operations & their codes
PEND_SHEET    = "PendingActions"
PEND_HEADER   = [
    "job_name","code","uid","defender_id","defender_name",
    "composition","scout_count","run_time","type","status"
]

def _ensure_deploy_sheet():
    rows = get_rows(DEPLOY_SHEET)
    if not rows or rows[0] != DEPLOY_HEADER:
        append_row(DEPLOY_SHEET, DEPLOY_HEADER)

def _ensure_pending_sheet():
    rows = get_rows(PEND_SHEET)
    if not rows or rows[0] != PEND_HEADER:
        append_row(PEND_SHEET, PEND_HEADER)

async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    # … your unchanged scouting report logic …
    data          = context.job.data
    chat_id       = int(data["uid"])
    defender_id   = data["defender_id"]
    defender_name = data["defender_name"]
    job_name      = context.job.name

    army = get_rows("Army")
    lines = [f"🔎 *Scouting Report: {defender_name}*"]
    total_power = 0
    for r in army[1:]:
        if r[0] != defender_id:
            continue
        key, cnt = r[1], int(r[2])
        if cnt <= 0:
            continue
        name, emoji, tier, pw, _ = UNITS[key]
        part = pw * cnt
        total_power += part
        lines.append(f"• {emoji} *{name}* (Tier {tier}) — {cnt} units ({part}⚔️)")

    if total_power:
        lines.append(f"\n⚔️ *Total Power:* {total_power}⚔️")
        text = "\n".join(lines)
    else:
        text = f"🔎 No troops detected at *{defender_name}*."

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

    # mark done
    _ensure_pending_sheet()
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[9] = "done"
            update_row(PEND_SHEET, idx, row)
            break

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    # … your unchanged combat resolution logic …
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    defender_name  = data["defender_name"]
    attacker_name  = data["attacker_name"]
    atk_i, def_i   = data["atk_i"], data["def_i"]
    comp           = data["composition"]
    ts             = data["timestamp"]
    job_name       = context.job.name

    # 1) pull back deployed detachment
    _ensure_deploy_sheet()
    deploy_rows = get_rows(DEPLOY_SHEET)
    recovered = {}
    for idx, row in enumerate(deploy_rows[1:], start=1):
        if row[0] != job_name:
            continue
        key, qty = row[2], int(row[3])
        if qty > 0:
            recovered[key] = recovered.get(key, 0) + qty
            row[3] = "0"
            update_row(DEPLOY_SHEET, idx, row)

    # 2) compute attacker power
    atk_power = sum(v * UNITS[k][3] for k, v in comp.items()) * random.uniform(0.9,1.1)

    # 3) compute defender garrison power
    def_rows = get_rows("Army")
    full_def = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k, v in full_def.items()) * random.uniform(0.9,1.1)

    # 4) win/loss & spoils
    players       = get_rows("Players")
    attacker_row  = players[atk_i]
    defender_row  = players[def_i]
    if atk_power > def_power:
        result = "win"
        spoils = max(1, int(defender_row[3])//10)
        msg_header = f"🏆 *{attacker_name}* defeated *{defender_name}*!\n💰 Loot: Stole {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) + spoils)
        defender_row[3] = str(int(defender_row[3]) - spoils)
    else:
        result = "loss"
        spoils = max(1, int(attacker_row[3])//20)
        msg_header = f"💥 *{attacker_name}* was defeated by *{defender_name}*!\n💸 Lost {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) - spoils)
        defender_row[3] = str(int(defender_row[3]) + spoils)

    # 5) survivors & casualties
    def survival(sent, own_p, opp_p):
        if own_p + opp_p == 0:
            return sent
        rate = own_p/(own_p+opp_p)
        return max(0, int(sent*rate))

    surv, cas = {}, {}
    for key, sent in comp.items():
        lost      = sent - survival(sent, atk_power, def_power)
        surv[key] = sent - lost
        cas[key]  = lost

    # 6) return survivors
    army_rows = get_rows("Army")
    for key, qty in surv.items():
        if qty <= 0:
            continue
        for i, r in enumerate(army_rows[1:], start=1):
            if r[0] == uid and r[1] == key:
                r[2] = str(int(r[2]) + qty)
                update_row("Army", i, r)
                break
        else:
            append_row("Army", [uid, key, str(qty)])

    # 7) persist players & log
    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [uid, str(defender_id), ts, result, str(spoils)])

    # 8) detailed battle report
    code = job_name.split("_")[-1]
    lines = [ msg_header, f"🏷️ Battle Code: `{code}`", "" ]
    lines.append("⚔️ *Your Detachment:*")
    for k, sent in comp.items():
        lines.append(f" • {UNITS[k][1]}×{sent} → Survivors {surv[k]}, Lost {cas[k]}")
    lines.append("")
    lines.append("🛡️ *Garrison Held:*")
    for k,v in full_def.items():
        lines.append(f" • {UNITS[k][1]}×{v}")
    text = "\n".join(lines)

    await context.bot.send_message(chat_id=int(uid), text=text, parse_mode=ParseMode.MARKDOWN)

    # 9) mark done
    _ensure_pending_sheet()
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[9] = "done"
            update_row(PEND_SHEET, idx, row)
            break

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only] [-c CODE]
    """
    user    = update.effective_user
    uid     = str(user.id)
    args    = context.args.copy()

    # remember if user included -u
    had_u = "-u" in args

    # ── 1) Cancellation? ────────────────────────────────────────────────────
    if "-c" in args:
        # … same cancellation block as above …
        # (remove scheduled job, mark cancelled, return troops)
        # then reply and return
        pass  # copy from above cancellation code

    # ── 2) Dispatch attack/scout ────────────────────────────────────────────
    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <Commander> -u infantry:10 … [-s <scouts>] [--scout-only]`",
            parse_mode=ParseMode.MARKDOWN
        )

    # Flags
    scout_only = "--scout-only" in args
    if scout_only: args.remove("--scout-only")

    # Target
    target = args.pop(0)

    # Scouts
    scout_count = 0
    if "-s" in args:
        i = args.index("-s")
        try:    scout_count = int(args[i+1])
        except: scout_count = 1
        args.pop(i)
        if i < len(args): args.pop(i)

    # Composition
    comp = {}
    if "-u" in args:
        i = args.index("-u")
        raw = []
        for tok in args[i+1:]:
            if tok.startswith("-"): break
            raw.append(tok)
        args = args[:i] + args[i+1+len(raw):]
        for pair in raw:
            if ":" in pair:
                k,v = pair.split(":",1)
                if k in UNITS and v.isdigit():
                    comp[k] = int(v)

    # If they used -u but no valid units, error
    if had_u and not comp and not scout_only:
        return await update.message.reply_text(
            "❗ I couldn’t parse any units after `-u`. Example: `-u infantry:3 tanks:2`",
            parse_mode=ParseMode.MARKDOWN
        )

    # Default → send all troops only if they never used -u
    if not comp and not scout_only and not had_u:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    # … now find players, deduct energy, record in sheets, schedule jobs, and send the UI …
    # (identical to your existing logic, nothing else changes)

handler = CommandHandler("attack", attack)
