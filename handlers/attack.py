# handlers/attack.py

import time
import random
import json
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from config import SPOIL_RATE, RESOURCE_COLUMNS
from sheets_service import get_rows as _get_rows, update_row as _update_row, append_row as _append_row
from utils.decorators import game_command
from modules.unit_manager import UNITS
from modules.challenge_manager import load_challenges, update_player_progress

# Safe wrappers around sheet operations
def get_rows(sheet_name):
    try:
        return _get_rows(sheet_name)
    except Exception:
        return []

def update_row(sheet_name, idx, row):
    try:
        _update_row(sheet_name, idx, row)
    except Exception:
        pass

def append_row(sheet_name, row):
    try:
        _append_row(sheet_name, row)
    except Exception:
        pass

# where we track troops in flight
DEPLOY_SHEET  = "DeployedArmy"
DEPLOY_HEADER = ["job_name", "uid", "unit_key", "quantity"]

# where we track pending operations & their codes
PEND_SHEET  = "PendingActions"
PEND_HEADER = [
    "job_name", "code", "uid", "defender_id", "defender_name",
    "composition", "scout_count", "run_time", "type", "status"
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
    pend = get_rows(PEND_SHEET)
    for idx, row in enumerate(pend[1:], start=1):
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

    # 1) Pull back in‑flight troops
    _ensure_deploy_sheet()
    deploy = get_rows(DEPLOY_SHEET)
    for idx, row in enumerate(deploy[1:], start=1):
        if row[0] != job_name:
            continue
        row[3] = "0"
        update_row(DEPLOY_SHEET, idx, row)

    # 2) Power rolls
    atk_power = sum(v * UNITS[k][3] for k, v in comp.items()) * random.uniform(0.9, 1.1)
    def_rows  = get_rows("Army")
    full_def  = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k, v in full_def.items()) * random.uniform(0.9, 1.1)

    # 3) Player rows
    players      = get_rows("Players")
    attacker_row = players[atk_i]
    defender_row = players[def_i]

    # 4) Determine outcome & steal resources
    if atk_power > def_power:
        result = "win"
        credit_stolen = max(1, int(int(defender_row[RESOURCE_COLUMNS['credits']]) * SPOIL_RATE))
        mineral_stolen = max(1, int(int(defender_row[RESOURCE_COLUMNS['minerals']]) * SPOIL_RATE))
        energy_stolen  = max(1, int(int(defender_row[RESOURCE_COLUMNS['energy']]) * SPOIL_RATE))

        # transfer
        defender_row[RESOURCE_COLUMNS['credits']]  = str(int(defender_row[RESOURCE_COLUMNS['credits']]) - credit_stolen)
        attacker_row[RESOURCE_COLUMNS['credits']]  = str(int(attacker_row[RESOURCE_COLUMNS['credits']]) + credit_stolen)
        defender_row[RESOURCE_COLUMNS['minerals']]= str(int(defender_row[RESOURCE_COLUMNS['minerals']]) - mineral_stolen)
        attacker_row[RESOURCE_COLUMNS['minerals']]= str(int(attacker_row[RESOURCE_COLUMNS['minerals']]) + mineral_stolen)
        defender_row[RESOURCE_COLUMNS['energy']]  = str(int(defender_row[RESOURCE_COLUMNS['energy']]) - energy_stolen)
        attacker_row[RESOURCE_COLUMNS['energy']]  = str(int(attacker_row[RESOURCE_COLUMNS['energy']]) + energy_stolen)

        msg_header = (
            f"🏆 *{attacker_name}* defeated *{defender_name}*!  \n"
            f"💰 +{credit_stolen}  ⛏️ +{mineral_stolen}  ⚡ +{energy_stolen}"
        )
    else:
        result = "loss"
        credit_lost  = max(1, int(int(attacker_row[RESOURCE_COLUMNS['credits']]) * SPOIL_RATE))
        mineral_lost = max(1, int(int(attacker_row[RESOURCE_COLUMNS['minerals']]) * SPOIL_RATE))
        energy_lost  = max(1, int(int(attacker_row[RESOURCE_COLUMNS['energy']]) * SPOIL_RATE))

        # transfer
        attacker_row[RESOURCE_COLUMNS['credits']]  = str(int(attacker_row[RESOURCE_COLUMNS['credits']]) - credit_lost)
        defender_row[RESOURCE_COLUMNS['credits']]  = str(int(defender_row[RESOURCE_COLUMNS['credits']]) + credit_lost)
        attacker_row[RESOURCE_COLUMNS['minerals']]= str(int(attacker_row[RESOURCE_COLUMNS['minerals']]) - mineral_lost)
        defender_row[RESOURCE_COLUMNS['minerals']]= str(int(defender_row[RESOURCE_COLUMNS['minerals']]) + mineral_lost)
        attacker_row[RESOURCE_COLUMNS['energy']]  = str(int(attacker_row[RESOURCE_COLUMNS['energy']]) - energy_lost)
        defender_row[RESOURCE_COLUMNS['energy']]  = str(int(defender_row[RESOURCE_COLUMNS['energy']]) + energy_lost)

        msg_header = (
            f"💥 *{attacker_name}* was defeated by *{defender_name}*!  \n"
            f"💸 -{credit_lost}  ⛏️ -{mineral_lost}  ⚡ -{energy_lost}"
        )

    # 5) Save players & log
    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [uid, str(defender_id), ts, result, str(credit_stolen if result=="win" else credit_lost)])

    # 6) Build & send battle report
    code = job_name.split("_")[-1]
    lines = [msg_header, f"🏷️ Battle Code: `{code}`", "", "⚔️ *Your Detachment:*"]
    for key, sent in comp.items():
        surv = max(0, int(sent * (atk_power / (atk_power + def_power))))
        lost = sent - surv
        lines.append(f" • {UNITS[key][1]}×{sent} → Survivors {surv}, Lost {lost}")
    lines.append("\n🛡️ *Garrison Held:*")
    for key, cnt in full_def.items():
        lines.append(f" • {UNITS[key][1]}×{cnt}")
    await context.bot.send_message(
        chat_id=int(uid),
        text="\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

    # 7) Mark done
    _ensure_pending_sheet()
    pend = get_rows(PEND_SHEET)
    for idx, row in enumerate(pend[1:], start=1):
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
        i = args.index("-c")
        try:
            code = args[i+1]
        except IndexError:
            return await update.message.reply_text(
                "❗ Usage to cancel: `/attack -c <CODE>`",
                parse_mode=ParseMode.MARKDOWN
            )

        _ensure_pending_sheet()
        pend = get_rows(PEND_SHEET)
        for idx, row in enumerate(pend[1:], start=1):
            job_name, prow_code, puid, *_ = row
            if puid == uid and prow_code == code and row[9] == "pending":
                try:
                    context.job_queue.scheduler.remove_job(job_name)
                except Exception:
                    pass
                row[9] = "cancelled"
                update_row(PEND_SHEET, idx, row)

                if row[8] == "attack":
                    _ensure_deploy_sheet()
                    dep = get_rows(DEPLOY_SHEET)
                    for d_idx, drow in enumerate(dep[1:], start=1):
                        if drow[0] == job_name:
                            key, qty = drow[2], int(drow[3])
                            if qty > 0:
                                army = get_rows("Army")
                                for a_i, ar in enumerate(army[1:], start=1):
                                    if ar[0] == uid and ar[1] == key:
                                        ar[2] = str(int(ar[2]) + qty)
                                        update_row("Army", a_i, ar)
                                        break
                                else:
                                    append_row("Army", [uid, key, str(qty)])
                            drow[3] = "0"
                            update_row(DEPLOY_SHEET, d_idx, drow)

                return await update.message.reply_text(
                    f"🚫 Operation `{code}` cancelled. Troops are returning home.",
                    parse_mode=ParseMode.MARKDOWN
                )

        return await update.message.reply_text(
            f"❗ No pending operation found with code `{code}`.",
            parse_mode=ParseMode.MARKDOWN
        )

    # 2) Normal dispatch
    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <Commander> -u infantry:5 tanks:2 ... [-s <scouts>] [--scout-only]`",
            parse_mode=ParseMode.MARKDOWN
        )

    scout_only = "--scout-only" in args
    if scout_only:
        args.remove("--scout-only")

    target = args.pop(0)

    scout_count = 0
    if "-s" in args:
        i = args.index("-s")
        try:
            scout_count = int(args[i+1])
        except Exception:
            scout_count = 1
        args.pop(i)
        if i < len(args):
            args.pop(i)

    comp = {}
    if "-u" in args:
        i = args.index("-u")
        raw = []
        for tok in args[i+1:]:
            if tok.startswith("-"):
                break
            raw.append(tok)
        args = args[:i] + args[i+1+len(raw):]
        for pair in raw:
            if ":" in pair:
                k, v = pair.split(":", 1)
                if k in UNITS and v.isdigit():
                    comp[k] = int(v)

    if not comp and not scout_only:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    players = get_rows("Players")
    attacker = defender = None
    atk_i = def_i = None
    for idx, r in enumerate(players[1:], start=1):
        if r[0] == uid:
            attacker, atk_i = r.copy(), idx
        if r[1].lower() == target.lower():
            defender, def_i = r.copy(), idx

    if not attacker:
        return await update.message.reply_text("❗ Run /start first.", parse_mode=ParseMode.MARKDOWN)
    if not defender:
        return await update.message.reply_text(f"❌ {target} not found.", parse_mode=ParseMode.MARKDOWN)
    if defender[0] == uid:
        return await update.message.reply_text("❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN)

    energy = int(attacker[5])
    cost   = (0 if scout_only else 5) + scout_count
    if energy < cost:
        return await update.message.reply_text(f"❌ Need {cost}⚡ but have {energy}⚡.", parse_mode=ParseMode.MARKDOWN)
    attacker[5] = str(energy - cost)
    update_row("Players", atk_i, attacker)

    _ensure_deploy_sheet()
    _ensure_pending_sheet()

    job_ts = str(int(time.time()))
    code   = f"{random.randint(0,99):02X}{chr(random.randint(65,90))}"
    job_name = None

    if not scout_only:
        army = get_rows("Army")
        job_name = f"attack_{uid}_{defender[0]}_{job_ts}_{code}"
        for key, qty in comp.items():
            for i, r in enumerate(army[1:], start=1):
                if r[0] == uid and r[1] == key:
                    r[2] = str(max(0, int(r[2]) - qty))
                    update_row("Army", i, r)
                    break
            append_row(DEPLOY_SHEET, [job_name, uid, key, str(qty)])

        run_at = (datetime.utcnow() + timedelta(minutes=30))\
                    .replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            job_name, code, uid, defender[0], defender[1],
            json.dumps(comp), "0", run_at, "attack", "pending"
        ])

    if scout_count > 0:
        scout_code = f"{random.randint(0,99):02X}{chr(random.randint(65,90))}"
        scout_name = f"scout_{uid}_{defender[0]}_{job_ts}_{scout_code}"

        context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=scout_name,
            data={"uid": uid, "defender_id": defender[0], "defender_name": defender[1]}
        )
        run_at = (datetime.utcnow() + timedelta(minutes=5))\
                    .replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            scout_name, scout_code, uid, defender[0], defender[1],
            json.dumps(comp), str(scout_count),
            run_at, "scout", "pending"
        ])

    if job_name:
        context.job_queue.run_once(
            combat_resolution_job,
            when=timedelta(minutes=30),
            name=job_name,
            data={
                "uid": uid,
                "defender_id": defender[0],
                "attacker_name": attacker[1],
                "defender_name": defender[1],
                "atk_i": atk_i,
                "def_i": def_i,
                "timestamp": job_ts,
                "composition": comp
            }
        )

    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    parts = [f"{UNITS[k][1]}×{v}" for k,v in comp.items()]
    if scout_count:
        parts.append(f"🔎 Scouts×{scout_count}")

    lines = ["⚔️ *Orders received!*", f"Target: *{defender[1]}*"]
    if scout_count:
        lines.append("• 🔎 Scouts arriving in 5 m")
    if job_name:
        lines.append("• 🏹 Attack arriving in 30 m")
    if parts:
        lines.append("\n• " + "  ".join(parts))
    if job_name:
        lines.append(f"\n🏷️ Code: `{code}` – use `/attack -c {code}` to cancel")

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("attack", attack)
