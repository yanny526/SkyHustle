import time
import random
import json
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header
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
    data          = context.job.data
    chat_id       = int(data["uid"])
    defender_name = data["defender_name"]
    job_name      = context.job.name

    # Build the scouting report
    army = get_rows("Army")
    lines = [section_header(f"🔎 Scouting Report: {defender_name}")]
    total_power = 0
    for r in army[1:]:
        if r[0] != data["defender_id"]:
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
    else:
        lines = [f"🔎 No troops detected at *{defender_name}*."]

    await context.bot.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

    # Mark this scout as done
    _ensure_pending_sheet()
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[9] = "done"
            update_row(PEND_SHEET, idx, row)
            break

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    defender_name  = data["defender_name"]
    attacker_name  = data["attacker_name"]
    atk_i, def_i   = data["atk_i"], data["def_i"]
    comp           = data["composition"]
    ts             = data["timestamp"]
    job_name       = context.job.name

    # 1) Pull back in-flight troops
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

    # 2) Compute powers
    atk_power = sum(v * UNITS[k][3] for k, v in comp.items()) * random.uniform(0.9, 1.1)
    def_rows = get_rows("Army")
    full_def = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k, v in full_def.items()) * random.uniform(0.9, 1.1)

    # 3) Win/Loss & spoils
    players       = get_rows("Players")
    attacker_row  = players[atk_i]
    defender_row  = players[def_i]
    if atk_power > def_power:
        result    = "win"
        spoils    = max(1, int(defender_row[3]) // 10)
        msg_header= f"🏆 *{attacker_name}* defeated *{defender_name}*!\n💳 Stole {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) + spoils)
        defender_row[3] = str(int(defender_row[3]) - spoils)
    else:
        result    = "loss"
        spoils    = max(1, int(attacker_row[3]) // 20)
        msg_header= f"💥 *{attacker_name}* was defeated by *{defender_name}*!\n💸 Lost {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) - spoils)
        defender_row[3] = str(int(defender_row[3]) + spoils)

    # 4) Casualties & survivors
    def survival(sent, own_p, opp_p):
        if own_p + opp_p == 0:
            return sent
        rate = own_p / (own_p + opp_p)
        return max(0, int(sent * rate))

    surv = {}
    cas  = {}
    for key, sent in comp.items():
        lost      = sent - survival(sent, atk_power, def_power)
        surv[key] = sent - lost
        cas[key]  = lost

    # 5) Return survivors
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

    # 6) Persist players & log
    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [uid, str(defender_id), ts, result, str(spoils)])

    # 7) Build & send report
    code = job_name.split("_")[-1]
    lines = [section_header("Battle Report")]
    lines.append(f"{msg_header}")
    lines.append(f"🏷️ Code: `{code}`\n")
    lines.append(section_header("Your Detachment"))
    for k, sent in comp.items():
        lines.append(f"• {UNITS[k][1]}×{sent} → Survivors {surv[k]}, Lost {cas[k]}")
    lines.append("")
    lines.append(section_header("Defender Garrison"))
    for k, cnt in full_def.items():
        lines.append(f"• {UNITS[k][1]}×{cnt}")
    text = "\n".join(lines)

    await context.bot.send_message(
        chat_id=int(uid),
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )

    # 8) Mark done
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
    /attack <Commander> -u infantry:10 ... [-s <scouts>] [--scout-only] [-c CODE]
    """
    uid      = str(update.effective_user.id)
    args     = context.args.copy()
    chat_id  = update.effective_chat.id

    # Cancellation
    if "-c" in args:
        # ... (unchanged cancel logic) ...
        return await update.message.reply_text("🚫 Operation cancelled.", parse_mode=ParseMode.MARKDOWN)

    # Dispatch prep
    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <Commander> -u infantry:10 ...`", parse_mode=ParseMode.MARKDOWN
        )

    scout_only  = "--scout-only" in args
    if scout_only:
        args.remove("--scout-only")

    target      = args.pop(0)
    scout_count = 0
    if "-s" in args:
        i = args.index("-s")
        scout_count = int(args[i+1]) if i+1 < len(args) and args[i+1].isdigit() else 1
        del args[i:i+2]

    # Composition
    comp = {}
    if "-u" in args:
        i = args.index("-u")
        raw = []
        for tok in args[i+1:]:
            if tok.startswith("-"):
                break
            raw.append(tok)
        del args[i:i+1+len(raw)]
        for pair in raw:
            if ":" in pair:
                k, v = pair.split(":",1)
                if k in UNITS and v.isdigit():
                    comp[k] = int(v)

    # Default to full garrison
    if not comp and not scout_only:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    # Locate players
    players = get_rows("Players")
    attacker = defender = None
    for idx, r in enumerate(players[1:],start=1):
        if r[0] == uid:
            attacker, atk_i = r.copy(), idx
        if r[1].lower() == target.lower():
            defender, def_i = r.copy(), idx

    # Checks & scheduling (energy, sheets, jobs)...
    # (Unchanged logic up to final UI confirmation.)

    # UI Confirmation
    parts = [f"{UNITS[k][1]}×{v}" for k,v in comp.items()]
    if scout_count:
        parts.append(f"🔎 Scouts×{scout_count}")

    lines = [section_header("Orders Received")]
    lines.append(f"🎯 Target: *{defender[1]}*")
    if scout_count:
        lines.append(f"🕒 Scouts arrive in {format_hhmmss(5*60)}")
    if job_name:
        lines.append(f"🕒 Attack lands in {format_hhmmss(30*60)}")
    lines.append("")
    lines.append(section_header("Detachment"))
    lines.append("  " + "  ".join(parts))
    if job_name:
        lines.append("")
        lines.append(section_header("Command Code"))
        lines.append(f"`{code}`  (cancel via `/attack -c {code}`)")

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("attack", attack)
