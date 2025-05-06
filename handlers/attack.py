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
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    defender_name  = data["defender_name"]
    attacker_name  = data["attacker_name"]
    atk_i, def_i   = data["atk_i"], data["def_i"]
    comp           = data["composition"]
    ts             = data["timestamp"]
    job_name       = context.job.name

    # 1) Pull back the in‑flight detachment
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

    # 2) Compute attacker detachment power
    atk_power = sum(v * UNITS[k][3] for k, v in comp.items()) * random.uniform(0.9, 1.1)

    # 3) Compute defender’s full garrison power
    def_rows = get_rows("Army")
    full_def = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k, v in full_def.items()) * random.uniform(0.9, 1.1)

    # 4) Resolve win/loss & spoils
    players       = get_rows("Players")
    attacker_row  = players[atk_i]
    defender_row  = players[def_i]
    if atk_power > def_power:
        result = "win"
        spoils = max(1, int(defender_row[3]) // 10)
        msg_header = f"🏆 *{attacker_name}* defeated *{defender_name}*!\n💰 Loot: Stole {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) + spoils)
        defender_row[3] = str(int(defender_row[3]) - spoils)
    else:
        result = "loss"
        spoils = max(1, int(attacker_row[3]) // 20)
        msg_header = f"💥 *{attacker_name}* was defeated by *{defender_name}*!\n💸 Lost {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) - spoils)
        defender_row[3] = str(int(defender_row[3]) + spoils)

    # 5) Casualty / survivor calculation
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

    # 6) Return survivors to your garrison
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

    # 7) Persist players & log
    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [uid, str(defender_id), ts, result, str(spoils)])

    # 8) Build & send detailed battle report
    #    (re‑use the same code you saw in /attack UI)
    code = job_name.split("_")[-1]  # the trailing CODE
    lines = [msg_header, f"🏷️ Battle Code: `{code}`", ""]
    lines.append("⚔️ *Your Detachment:*")
    for k, sent in comp.items():
        lines.append(f" • {UNITS[k][1]}×{sent} → Survivors {surv[k]}, Lost {cas[k]}")
    lines.append("")
    lines.append("🛡️ *Garrison Held:*")
    for k, cnt in full_def.items():
        lines.append(f" • {UNITS[k][1]}×{cnt}")
    text = "\n".join(lines)

    await context.bot.send_message(
        chat_id=int(uid),
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )

    # 9) Mark the pending attack as done
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
            job_name, prow_code, puid, *_rest = row
            if puid == uid and prow_code == code and row[9] == "pending":
                # unschedule
                try:
                    context.job_queue.scheduler.remove_job(job_name)
                except Exception:
                    pass
                # mark cancelled
                row[9] = "cancelled"
                update_row(PEND_SHEET, idx, row)

                # return troops if it was an attack
                if row[8] == "attack":
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
            "❗ Usage: `/attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only]`",
            parse_mode=ParseMode.MARKDOWN
        )

    scout_only = "--scout-only" in args
    if scout_only:
        args.remove("--scout-only")

    # target
    target = args.pop(0)

    # scouts
    scout_count = 0
    if "-s" in args:
        i = args.index("-s")
        try:
            scout_count = int(args[i+1])
        except:
            scout_count = 1
        args.pop(i)
        if i < len(args):
            args.pop(i)

    # custom composition
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

    # default to everything in garrison
    if not comp and not scout_only:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    # locate players
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

    # energy check
    energy = int(attacker[5])
    cost   = (0 if scout_only else 5) + scout_count
    if energy < cost:
        return await update.message.reply_text(f"❌ Need {cost}⚡ but have {energy}⚡.", parse_mode=ParseMode.MARKDOWN)
    attacker[5] = str(energy - cost)
    update_row("Players", atk_i, attacker)

    # prepare sheets
    _ensure_deploy_sheet()
    _ensure_pending_sheet()

    job_ts = str(int(time.time()))
    code   = f"{random.randint(0,99):02X}{chr(random.randint(65,90))}"
    job_name = None

    if not scout_only:
        army = get_rows("Army")
        job_name = f"attack_{uid}_{defender[0]}_{job_ts}_{code}"
        for key, qty in comp.items():
            # remove from garrison
            for i, r in enumerate(army[1:], start=1):
                if r[0] == uid and r[1] == key:
                    r[2] = str(max(0, int(r[2]) - qty))
                    update_row("Army", i, r)
                    break
            # log in-flight
            append_row(DEPLOY_SHEET, [job_name, uid, key, str(qty)])

        # record pending attack
        run_at = (datetime.utcnow() + timedelta(minutes=30))\
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
        run_at = (datetime.utcnow() + timedelta(minutes=5))\
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

    # track daily attacks challenge
    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    # UI confirmation
    parts = [f"{UNITS[k][1]}×{v}" for k,v in comp.items()]
    if scout_count:
        parts.append(f"🔎 Scouts×{scout_count}")

    lines = ["⚔️ *Orders received!*",
             f"Target: *{defender[1]}*"]
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
