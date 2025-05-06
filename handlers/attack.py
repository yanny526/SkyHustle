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
DEPLOY_SHEET    = "DeployedArmy"
DEPLOY_HEADER   = ["job_name","uid","unit_key","quantity"]

# where we track pending operations & their codes
PEND_SHEET      = "PendingActions"
PEND_HEADER     = [
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

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    # … your unchanged combat resolution logic …

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only] [-c CODE]
    """
    user    = update.effective_user
    uid     = str(user.id)
    args    = context.args.copy()
    chat_id = update.effective_chat.id

    # ── 1) Cancellation flag? ───────────────────────────────────────────────
    if "-c" in args:
        i = args.index("-c")
        try:
            code = args[i+1]
        except IndexError:
            return await update.message.reply_text(
                "❗ Usage to cancel: `/attack -c <CODE>`",
                parse_mode=ParseMode.MARKDOWN
            )
        # find and cancel
        _ensure_pending_sheet()
        pend = get_rows(PEND_SHEET)
        for idx, row in enumerate(pend[1:], start=1):
            job_name, prow_code, puid, _, _, comp, scouts, rt, typ, status = row
            if puid == uid and prow_code == code and status == "pending":
                # unschedule
                try:
                    context.job_queue.scheduler.remove_job(job_name)
                except Exception:
                    pass
                # mark cancelled
                row[9] = "cancelled"   # status is last column
                update_row(PEND_SHEET, idx, row)

                # return troops if it was an attack
                if typ == "attack":
                    _ensure_deploy_sheet()
                    dep = get_rows(DEPLOY_SHEET)
                    for d_idx, drow in enumerate(dep[1:], start=1):
                        if drow[0] == job_name:
                            key, qty = drow[2], int(drow[3])
                            if qty > 0:
                                # give them back
                                army = get_rows("Army")
                                for a_i, ar in enumerate(army[1:], start=1):
                                    if ar[0] == uid and ar[1] == key:
                                        ar[2] = str(int(ar[2]) + qty)
                                        update_row("Army", a_i, ar)
                                        break
                                else:
                                    append_row("Army", [uid, key, str(qty)])
                            # zero out deploy row
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

    # ── 2) Normal attack/scout dispatch ─────────────────────────────────────
    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only]`",
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

    # default: everything
    if not comp and not scout_only:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    # Locate players
    players = get_rows("Players")
    attacker = defender = None
    atk_i = def_i = None
    for idx, r in enumerate(players[1:], start=1):
        if r[0] == uid:       attacker, atk_i = r.copy(), idx
        if r[1].lower() == target.lower():
            defender, def_i = r.copy(), idx

    if not attacker:
        return await update.message.reply_text(
            "❗ Run /start first.", parse_mode=ParseMode.MARKDOWN
        )
    if not defender:
        return await update.message.reply_text(
            f"❌ {target} not found.", parse_mode=ParseMode.MARKDOWN
        )
    if defender[0] == uid:
        return await update.message.reply_text(
            "❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN
        )

    # Energy cost & deduction
    energy = int(attacker[5])
    cost   = (0 if scout_only else 5) + scout_count
    if energy < cost:
        return await update.message.reply_text(
            f"❌ Need {cost}⚡ but have {energy}⚡.",
            parse_mode=ParseMode.MARKDOWN
        )
    attacker[5] = str(energy - cost)
    update_row("Players", atk_i, attacker)

    # Deduct & record deployed troops
    job_ts   = str(int(time.time()))
    code     = f"{random.randint(0,99):02X}{chr(random.randint(65,90))}"
    job_name = None

    _ensure_deploy_sheet()
    _ensure_pending_sheet()

    if not scout_only:
        army = get_rows("Army")
        job_name = f"attack_{uid}_{defender[0]}_{job_ts}_{code}"
        for key, qty in comp.items():
            # remove from Army
            for i,r in enumerate(army[1:], start=1):
                if r[0] == uid and r[1] == key:
                    r[2] = str(max(0, int(r[2]) - qty))
                    update_row("Army", i, r)
                    break
            # record to DeployedArmy
            append_row(DEPLOY_SHEET, [job_name, uid, key, str(qty)])

        # persist pending
        run_at = (datetime.utcnow() + timedelta(minutes=30)) \
                    .replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            job_name, code, uid, defender[0], defender[1],
            json.dumps(comp), "0", run_at, "attack", "pending"
        ])

    if scout_count > 0:
        scout_code = f"{random.randint(0,99):02X}{chr(random.randint(65,90))}"
        scout_name = f"scout_{uid}_{defender[0]}_{job_ts}_{scout_code}"
        # schedule scout
        context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=scout_name,
            data={"uid": uid, "defender_id": defender[0], "defender_name": defender[1]}
        )
        run_at = (datetime.utcnow() + timedelta(minutes=5)) \
                    .replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            scout_name, scout_code, uid, defender[0], defender[1],
            json.dumps(comp), str(scout_count),
            run_at, "scout", "pending"
        ])

    if job_name:
        # schedule combat
        context.job_queue.run_once(
            combat_resolution_job,
            when=timedelta(minutes=30),
            name=job_name,
            data={
                "uid": uid, "defender_id": defender[0],
                "attacker_name": attacker[1],
                "defender_name": defender[1],
                "atk_i": atk_i, "def_i": def_i,
                "timestamp": job_ts, "composition": comp
            }
        )

    # track challenges
    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    # Confirmation UI
    parts = [f"{UNITS[k][1]}×{v}" for k,v in comp.items()] if comp else []
    if scout_count: parts.append(f"🔎 Scouts×{scout_count}")
    lines = ["⚔️ *Orders received!*", f"Target: *{defender[1]}*"]
    if scout_count: lines.append("• 🔎 Scouts arriving in 5 m")
    if job_name:    lines.append("• 🏹 Attack arriving in 30 m")
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
