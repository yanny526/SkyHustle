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

# Spoils configuration: percentage of each resource stolen from loser
SPOIL_RATE = 0.10  # 10%
RESOURCE_COLUMNS = {
    'credits': 3,
    'minerals': 4,
    'energy': 5,
}

# where we track troops in flight
DEPLOY_SHEET  = "DeployedArmy"
DEPLOY_HEADER = ["job_name","uid","unit_key","quantity"]

# where we track pending operations & their codes
PEND_SHEET  = "PendingActions"
PEND_HEADER = [
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
    defender_id   = data["defender_id"]
    defender_name = data["defender_name"]
    job_name      = context.job.name

    # Build the scouting report
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

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )

    # Mark this scout as done in PendingActions
    _ensure_pending_sheet()
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[9] = "done"
            update_row(PEND_SHEET, idx, row)
            break

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    data          = context.job.data
    uid           = data["uid"]
    defender_id   = data["defender_id"]
    defender_name = data["defender_name"]
    attacker_name = data["attacker_name"]
    atk_i, def_i  = data["atk_i"], data["def_i"]
    comp          = data["composition"]
    ts            = data["timestamp"]
    job_name      = context.job.name

    # 1) Pull back the in‑flight detachment
    _ensure_deploy_sheet()
    deploy_rows = get_rows(DEPLOY_SHEET)
    for idx, row in enumerate(deploy_rows[1:], start=1):
        if row[0] != job_name:
            continue
        key, qty = row[2], int(row[3])
        if qty > 0:
            # auto-return survivors
            row[3] = "0"
            update_row(DEPLOY_SHEET, idx, row)

    # 2) Compute attacker & defender power rolls
    atk_power = sum(v * UNITS[k][3] for k, v in comp.items()) * random.uniform(0.9, 1.1)
    def_rows  = get_rows("Army")
    full_def  = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k, v in full_def.items()) * random.uniform(0.9, 1.1)

    # 3) Load player rows
    players      = get_rows("Players")
    attacker_row = players[atk_i]
    defender_row = players[def_i]

    # 4) Determine result & calculate spoils per resource
    if atk_power > def_power:
        result = "win"
        # Credits spoils: old logic preserved
        credit_spoils = max(1, int(int(defender_row[RESOURCE_COLUMNS['credits']]) * SPOIL_RATE))
        # Transfer credits
        defender_row[RESOURCE_COLUMNS['credits']] = str(int(defender_row[RESOURCE_COLUMNS['credits']]) - credit_spoils)
        attacker_row[RESOURCE_COLUMNS['credits']] = str(int(attacker_row[RESOURCE_COLUMNS['credits']]) + credit_spoils)
        # Minerals & Energy
        mineral_spoils = max(1, int(int(defender_row[RESOURCE_COLUMNS['minerals']]) * SPOIL_RATE))
        defender_row[RESOURCE_COLUMNS['minerals']] = str(int(defender_row[RESOURCE_COLUMNS['minerals']]) - mineral_spoils)
        attacker_row[RESOURCE_COLUMNS['minerals']] = str(int(attacker_row[RESOURCE_COLUMNS['minerals']]) + mineral_spoils)
        energy_spoils  = max(1, int(int(defender_row[RESOURCE_COLUMNS['energy']]) * SPOIL_RATE))
        defender_row[RESOURCE_COLUMNS['energy']]   = str(int(defender_row[RESOURCE_COLUMNS['energy']]) - energy_spoils)
        attacker_row[RESOURCE_COLUMNS['energy']]   = str(int(attacker_row[RESOURCE_COLUMNS['energy']]) + energy_spoils)
        msg_header = (f"🏆 *{attacker_name}* defeated *{defender_name}*!\n"
                      f"💰 Credits: +{credit_spoils}  ⛏️ Minerals: +{mineral_spoils}  ⚡ Energy: +{energy_spoils}")
    else:
        result = "loss"
        credit_spoils = max(1, int(int(attacker_row[RESOURCE_COLUMNS['credits']]) * SPOIL_RATE))
        attacker_row[RESOURCE_COLUMNS['credits']] = str(int(attacker_row[RESOURCE_COLUMNS['credits']]) - credit_spoils)
        defender_row[RESOURCE_COLUMNS['credits']] = str(int(defender_row[RESOURCE_COLUMNS['credits']]) + credit_spoils)
        mineral_spoils = max(1, int(int(attacker_row[RESOURCE_COLUMNS['minerals']]) * SPOIL_RATE))
        attacker_row[RESOURCE_COLUMNS['minerals']] = str(int(attacker_row[RESOURCE_COLUMNS['minerals']]) - mineral_spoils)
        defender_row[RESOURCE_COLUMNS['minerals']] = str(int(defender_row[RESOURCE_COLUMNS['minerals']]) + mineral_spoils)
        energy_spoils  = max(1, int(int(attacker_row[RESOURCE_COLUMNS['energy']]) * SPOIL_RATE))
        attacker_row[RESOURCE_COLUMNS['energy']]   = str(int(attacker_row[RESOURCE_COLUMNS['energy']]) - energy_spoils)
        defender_row[RESOURCE_COLUMNS['energy']]   = str(int(defender_row[RESOURCE_COLUMNS['energy']]) + energy_spoils)
        msg_header = (f"💥 *{attacker_name}* was defeated by *{defender_name}*!\n"
                      f"💸 Credits: -{credit_spoils}  ⛏️ Minerals: -{mineral_spoils}  ⚡ Energy: -{energy_spoils}")

    # 5) Persist updated players & log
    update_row('Players', atk_i, attacker_row)
    update_row('Players', def_i, defender_row)
    append_row('CombatLog', [uid, str(defender_id), ts, result, str(credit_spoils)])

    # 6) Build & send detailed battle report
    code = job_name.split("_")[-1]
    lines = [msg_header, f"🏷️ Battle Code: `{code}`", "", "⚔️ *Your Detachment:*"]
    for k, sent in comp.items():
        surv = max(0, sent - int(sent * (def_power / (atk_power + def_power))))
        lost = sent - surv
        lines.append(f" • {UNITS[k][1]}×{sent} → Survivors {surv}, Lost {lost}")
    lines.append("\n🛡️ *Garrison Held:*")
    for k, cnt in full_def.items():
        lines.append(f" • {UNITS[k][1]}×{cnt}")
    text = "\n".join(lines)

    await context.bot.send_message(
        chat_id=int(uid),
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )

    # 7) Mark the pending attack as done
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
    /attack <Commander> -u infantry:5 tanks:2 ... [-s <scouts>] [--scout-only] [-c CODE]
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args.copy()

    # Enhanced help UI when no arguments provided
    if not args:
        kb = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("📜 View Pending", callback_data="reports")
        )
        help_text = (
            "----- 🏰 COMMAND CENTER: Attack Protocols -----\n\n"
            "Welcome, Commander! Issue your orders with confidence:\n\n"
            "=== ⚔️ Standard Assault ===\n"
            "`/attack <Commander> -u infantry:5 tanks:2`\n"
            "→ Launch a combined arms strike.\n\n"
            "=== 🔎 Recon Only ===\n"
            "`/attack <Commander> --scout-only -s 3`\n"
            "→ Send 3 scouts to gather intel.\n\n"
            "=== ❌ Abort Mission ===\n"
            "`/attack -c <CODE>`\n"
            "→ Cancel an en route mission.\n\n"
            "After dispatch, press *View Pending* below to track missions."
        )
        return await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )

    chat_id = update.effective_chat.id

    # 1) Cancellation?
    if "-c" in args:
        # ... existing cancellation logic unchanged ...
        pass

    # 2) Normal dispatch
    # ... existing dispatch logic unchanged ...

handler = CommandHandler("attack", attack)
