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
    "job_name","uid","defender_id","defender_name","composition",
    "scout_count","run_time","type","status"
]

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

    # Build scouting report
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
        parse_mode=ParseMode.MARKDOWN,
    )

    # Mark done in sheet
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[8] = "done"
            update_row(PEND_SHEET, idx, row)
            break

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

    # Compute attacker detachment power
    atk_power = sum(v * UNITS[k][3] for k, v in comp.items()) * random.uniform(0.9, 1.1)

    # Defender uses full army
    def_rows = get_rows("Army")
    def_comp = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k, v in def_comp.items()) * random.uniform(0.9, 1.1)

    players      = get_rows("Players")
    attacker_row = players[atk_i]
    defender_row = players[def_i]

    if atk_power > def_power:
        result = "win"
        spoils = max(1, int(defender_row[3]) // 10)
        msg = f"🏆 *{attacker_name}* defeated *{defender_name}*! 💰 Stole {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) + spoils)
        defender_row[3] = str(int(defender_row[3]) - spoils)
    else:
        result = "loss"
        spoils = max(1, int(attacker_row[3]) // 20)
        msg = f"💥 *{attacker_name}* was defeated by *{defender_name}*! 💸 Lost {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) - spoils)
        defender_row[3] = str(int(defender_row[3]) + spoils)

    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [data["uid"], str(defender_id), timestamp, result, str(spoils)])

    await context.bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode=ParseMode.MARKDOWN
    )

    # Mark done
    rows = get_rows(PEND_SHEET)
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == job_name:
            row[8] = "done"
            update_row(PEND_SHEET, idx, row)
            break

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only]
    """
    user    = update.effective_user
    uid     = str(user.id)
    args    = context.args.copy()
    chat_id = update.effective_chat.id

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <Commander> -u infantry:10 tanks:5 ... [-s <scouts>] [--scout-only]`",
            parse_mode=ParseMode.MARKDOWN
        )

    # Flags
    scout_only  = False
    if "--scout-only" in args:
        scout_only = True
        args.remove("--scout-only")

    target      = args.pop(0)

    # Parse scouts
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

    # Parse units
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

    # Default: all troops if not specifying units or scout-only
    if not comp and not scout_only:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    # Locate players
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

    # Energy cost & deduction
    energy = int(attacker[5])
    cost   = (0 if scout_only else 5) + scout_count
    if energy < cost:
        return await update.message.reply_text(
            f"❌ Need {cost}⚡ but have {energy}⚡.", parse_mode=ParseMode.MARKDOWN
        )
    attacker[5] = str(energy - cost)
    update_row("Players", atk_i, attacker)

    # Deduct troops for main attack
    if not scout_only:
        army = get_rows("Army")
        for key, qty in comp.items():
            for i, r in enumerate(army[1:], start=1):
                if r[0] == uid and r[1] == key:
                    new = max(0, int(r[2]) - qty)
                    r[2] = str(new)
                    update_row("Army", i, r)
                    break

    ts = str(int(time.time()))
    _ensure_pending_sheet()

    # Schedule scouts
    if scout_count > 0:
        j = context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=f"scout_{uid}_{defender[0]}_{ts}",
            data={"uid": uid, "defender_id": defender[0], "defender_name": defender[1]}
        )
        run_time = (datetime.utcnow() + timedelta(minutes=5)).replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            j.name, uid, defender[0], defender[1],
            json.dumps(comp), str(scout_count),
            run_time, "scout", "pending"
        ])

    # Schedule main attack
    if not scout_only:
        j = context.job_queue.run_once(
            combat_resolution_job,
            when=timedelta(minutes=30),
            name=f"attack_{uid}_{defender[0]}_{ts}",
            data={
                "uid": uid, "defender_id": defender[0],
                "attacker_name": attacker[1], "defender_name": defender[1],
                "atk_i": atk_i, "def_i": def_i,
                "timestamp": ts, "composition": comp
            }
        )
        run_time = (datetime.utcnow() + timedelta(minutes=30)).replace(tzinfo=timezone.utc).isoformat()
        append_row(PEND_SHEET, [
            j.name, uid, defender[0], defender[1],
            json.dumps(comp), "0",
            run_time, "attack", "pending"
        ])

    # Track challenges
    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    # UI confirmation
    parts = [f"{UNITS[k][1]}×{v}" for k, v in comp.items()] if comp else []
    if scout_count:
        parts.append(f"🔎 Scouts×{scout_count}")
    lines = ["⚔️ *Orders received!*"]
    lines.append(f"Target: *{defender[1]}*")
    if scout_count:
        lines.append("• 🔎 Scouts arriving in 5m")
    if not scout_only:
        lines.append("• 🏹 Attack arriving in 30m")
    if parts:
        lines.append("\n• " + "  ".join(parts))

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("attack", attack)
