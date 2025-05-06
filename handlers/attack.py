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

# new sheet where we track troops in flight
DEPLOY_SHEET   = "DeployedArmy"
DEPLOY_HEADER  = ["job_name","uid","unit_key","quantity"]

def _ensure_deploy_sheet():
    rows = get_rows(DEPLOY_SHEET)
    if not rows or rows[0] != DEPLOY_HEADER:
        append_row(DEPLOY_SHEET, DEPLOY_HEADER)

async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    # unchanged...

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    data        = context.job.data
    uid         = data["uid"]
    defender_id = data["defender_id"]
    defender    = data["defender_name"]
    attacker    = data["attacker_name"]
    atk_i, def_i= data["atk_i"], data["def_i"]
    comp        = data["composition"]
    ts          = data["timestamp"]
    job_name    = context.job.name

    # — pull back deployed detachment for this job
    _ensure_deploy_sheet()
    deploy_rows = get_rows(DEPLOY_SHEET)
    recovered = {}
    for idx, row in enumerate(deploy_rows[1:], start=1):
        if row[0] != job_name:
            continue
        key, qty = row[2], int(row[3])
        if qty > 0:
            recovered[key] = recovered.get(key, 0) + qty
            # zero it out to mark “returned”
            row[3] = "0"
            update_row(DEPLOY_SHEET, idx, row)

    # compute attacker power (detachment only)
    atk_power = sum(v * UNITS[k][3] for k,v in comp.items()) * random.uniform(0.9,1.1)
    # defender uses full garrison
    def_rows = get_rows("Army")
    full_def = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_power = sum(v * UNITS[k][3] for k,v in full_def.items()) * random.uniform(0.9,1.1)

    # decide win/loss & spoils
    players       = get_rows("Players")
    attacker_row  = players[atk_i]
    defender_row  = players[def_i]
    if atk_power > def_power:
        result = "win"
        spoils = max(1, int(defender_row[3])//10)
        msg_header = f"🏆 *{attacker}* defeated *{defender}*!\n💰 Loot: Stole {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) + spoils)
        defender_row[3] = str(int(defender_row[3]) - spoils)
    else:
        result = "loss"
        spoils = max(1, int(attacker_row[3])//20)
        msg_header = f"💥 *{attacker}* was defeated by *{defender}*!\n💸 Lost {spoils} credits."
        attacker_row[3] = str(int(attacker_row[3]) - spoils)
        defender_row[3] = str(int(defender_row[3]) + spoils)

    # survivors formula: each side keeps proportion of original detachment
    def survival(detach, own_power, opp_power):
        if own_power+opp_power == 0:
            return detach
        rate = own_power / (own_power + opp_power)
        return max(0, int(detach * rate))
    surv = {}
    cas  = {}
    for key, sent in comp.items():
        lost = sent - survival(sent, atk_power, def_power)
        surv[key] = sent - lost
        cas[key]  = lost

    #  — return survivors to home Army
    army_rows = get_rows("Army")
    for key, qty in surv.items():
        if qty <= 0:
            continue
        # find existing row
        for i, r in enumerate(army_rows[1:], start=1):
            if r[0]==uid and r[1]==key:
                r[2] = str(int(r[2]) + qty)
                update_row("Army", i, r)
                break
        else:
            append_row("Army", [uid, key, str(qty)])

    # persist Players & combat log
    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [uid, str(defender_id), ts, result, str(spoils)])

    # build detailed report
    code = f"{random.randint(0,99):02X}{chr(random.randint(65,90))}"
    lines = [ msg_header, f"🏷️ Battle Code: `{code}`", "" ]
    lines.append("⚔️ *Your Detachment:*")
    for k,v in comp.items():
        lines.append(f" • {UNITS[k][1]}×{v} → Survivors {surv[k]}, Lost {cas[k]}")
    lines.append("")
    lines.append("🛡️ *Garrison Held:*")
    for k, v in full_def.items():
        lines.append(f" • {UNITS[k][1]}×{v}")
    text = "\n".join(lines)

    await context.bot.send_message(
        chat_id=int(uid),
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )

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

    # find players...
    players = get_rows("Players")
    attacker = defender = None
    atk_i = def_i = None
    for idx, r in enumerate(players[1:], start=1):
        if r[0] == uid:       attacker, atk_i = r.copy(), idx
        if r[1].lower()==target.lower(): defender, def_i = r.copy(), idx

    if not attacker:
        return await update.message.reply_text("❗ Run /start first.", parse_mode=ParseMode.MARKDOWN)
    if not defender:
        return await update.message.reply_text(f"❌ {target} not found.", parse_mode=ParseMode.MARKDOWN)
    if defender[0] == uid:
        return await update.message.reply_text("❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN)

    # energy & cost
    energy = int(attacker[5])
    cost   = (0 if scout_only else 5) + scout_count
    if energy < cost:
        return await update.message.reply_text(f"❌ Need {cost}⚡ but have {energy}⚡.", parse_mode=ParseMode.MARKDOWN)
    attacker[5] = str(energy - cost)
    update_row("Players", atk_i, attacker)

    # deduct from Army and log into DeployedArmy
    if not scout_only:
        army = get_rows("Army")
        _ensure_deploy_sheet()
        ts = str(int(time.time()))
        job_name = f"attack_{uid}_{defender[0]}_{ts}"
        for key,qty in comp.items():
            # remove from Army
            for i,r in enumerate(army[1:],start=1):
                if r[0]==uid and r[1]==key:
                    new = max(0,int(r[2]) - qty)
                    r[2] = str(new)
                    update_row("Army", i, r)
                    break
            # record to DeployedArmy
            append_row(DEPLOY_SHEET, [job_name, uid, key, str(qty)])
    else:
        job_name = None

    # schedule jobs exactly as before (scouting + combat), passing composition
    # ... (unchanged scheduling block) ...

    # UI confirmation
    parts = [f"{UNITS[k][1]}×{v}" for k,v in comp.items()]
    if scout_count: parts.append(f"🔎 Scouts×{scout_count}")
    lines = ["⚔️ *Orders received!*", f"Target: *{defender[1]}*"]
    if scout_count: lines.append("• 🔎 Scouts arriving in 5 m")
    if not scout_only: lines.append("• 🏹 Attack arriving in 30 m")
    if parts:
        lines.append("\n• " + "  ".join(parts))

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text("\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("attack", attack)
