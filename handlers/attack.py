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

PEND_SHEET    = "PendingActions"
PEND_HEADER   = [
    "job_name","uid","defender_id","defender_name","composition",
    "scout_count","run_time","type","status"
]
DEPLOY_SHEET  = "DeployedArmy"

# derive an HP pool for each unit (here: HP = 2x its power)
UNIT_HP = {k: v[3] * 2 for k, v in UNITS.items()}


def _ensure_pending_sheet():
    rows = get_rows(PEND_SHEET)
    if not rows or rows[0] != PEND_HEADER:
        append_row(PEND_SHEET, PEND_HEADER)


async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    # unchanged...
    ...

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    data          = context.job.data
    uid           = data["uid"]
    chat_id       = int(uid)
    defender_id   = data["defender_id"]
    defender_name = data["defender_name"]
    attacker_name = data["attacker_name"]
    atk_i, def_i  = data["atk_i"], data["def_i"]
    comp          = data["composition"]     # dict unit_key → qty
    timestamp     = data["timestamp"]
    job_name      = context.job.name

    # ─── Build HP pools & DPS ───────────────────────────────────────────────
    atk_hp_pool = sum(qty * UNIT_HP[k]   for k, qty in comp.items())
    atk_dps     = sum(qty * UNITS[k][3]  for k, qty in comp.items())
    # Defender garrison
    def_rows    = get_rows("Army")
    def_comp    = {r[1]: int(r[2]) for r in def_rows[1:] if r[0] == defender_id}
    def_hp_pool = sum(qty * UNIT_HP[k]   for k, qty in def_comp.items())
    def_dps     = sum(qty * UNITS[k][3]  for k, qty in def_comp.items())

    # ─── Simulate up to 3 rounds ────────────────────────────────────────────
    atk_hp = atk_hp_pool
    def_hp = def_hp_pool
    for _ in range(3):
        atk_damage = atk_dps * random.uniform(0.9, 1.1)
        def_damage = def_dps * random.uniform(0.9, 1.1)
        def_hp = max(0, def_hp - atk_damage)
        atk_hp = max(0, atk_hp - def_damage)
        if atk_hp == 0 or def_hp == 0:
            break

    # ─── Compute survivors & casualties ────────────────────────────────────
    att_ratio = (atk_hp / atk_hp_pool) if atk_hp_pool > 0 else 0
    def_ratio = (def_hp / def_hp_pool) if def_hp_pool > 0 else 0

    survivors_att = {k: int(qty * att_ratio) for k, qty in comp.items()}
    casualties_att = {k: comp[k] - survivors_att[k] for k in comp}

    survivors_def = {k: int(qty * def_ratio) for k, qty in def_comp.items()}
    casualties_def = {k: def_comp[k] - survivors_def[k] for k in def_comp}

    # ─── Update sheets: return survivors, apply casualties ────────────────
    # 1) Remove deployed troops from DeployedArmy
    dep_rows = get_rows(DEPLOY_SHEET)
    for idx, row in enumerate(dep_rows[1:], start=1):
        if row[0] == uid:
            key = row[1]
            qty = int(row[2])
            used = comp.get(key, 0)
            new  = max(0, qty - used)
            row[2] = str(new)
            update_row(DEPLOY_SHEET, idx, row)

    # 2) Attacker: survivors go back into Army
    army_rows = get_rows("Army")
    for key, surv in survivors_att.items():
        # find existing
        for idx, r in enumerate(army_rows[1:], start=1):
            if r[0] == uid and r[1] == key:
                r[2] = str(int(r[2]) + surv)
                update_row("Army", idx, r)
                break
        else:
            append_row("Army", [uid, key, str(surv)])

    # 3) Defender: subtract casualties from Army
    for key, lost in casualties_def.items():
        for idx, r in enumerate(army_rows[1:], start=1):
            if r[0] == defender_id and r[1] == key:
                r[2] = str(max(0, int(r[2]) - lost))
                update_row("Army", idx, r)
                break

    # 4) Credits spoils
    players      = get_rows("Players")
    attacker_row = players[atk_i]
    defender_row = players[def_i]
    if atk_hp > def_hp:
        # attacker wins
        spoils = max(1, int(defender_row[3]) // 10)
        msg = (
            f"🏆 *{attacker_name}* prevails!\n"
            f"💰 Stole {spoils} credits.\n\n"
            "🗡 *Casualties:* " +
            "  ".join(f"{UNITS[k][1]}−{casualties_att[k]}" for k in casualties_att if casualties_att[k])
            + "\n"
            "🛡️ *Defender lost:* " +
            "  ".join(f"{UNITS[k][1]}−{casualties_def[k]}" for k in casualties_def if casualties_def[k])
        )
        attacker_row[3] = str(int(attacker_row[3]) + spoils)
        defender_row[3] = str(int(defender_row[3]) - spoils)
    else:
        # defender holds
        spoils = max(1, int(attacker_row[3]) // 20)
        msg = (
            f"💥 *{attacker_name}* was repulsed!\n"
            f"💸 Lost {spoils} credits.\n\n"
            "🗡 *Casualties:* " +
            "  ".join(f"{UNITS[k][1]}−{casualties_att[k]}" for k in casualties_att if casualties_att[k])
            + "\n"
            "🛡️ *Defender lost:* " +
            "  ".join(f"{UNITS[k][1]}−{casualties_def[k]}" for k in casualties_def if casualties_def[k])
        )
        attacker_row[3] = str(int(attacker_row[3]) - spoils)
        defender_row[3] = str(int(defender_row[3]) + spoils)

    update_row("Players", atk_i, attacker_row)
    update_row("Players", def_i, defender_row)
    append_row("CombatLog", [uid, defender_id, timestamp, "win" if atk_hp>def_hp else "loss", str(spoils)])

    # ─── Send detailed result DM ────────────────────────────────────────────
    await context.bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode=ParseMode.MARKDOWN
    )

    # ─── Mark done in pending sheet ────────────────────────────────────────
    pend = get_rows(PEND_SHEET)
    for idx, row in enumerate(pend[1:], start=1):
        if row[0] == job_name:
            row[8] = "done"
            update_row(PEND_SHEET, idx, row)
            break


@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # unchanged scheduling & soldier deduction, plus:
    # ─ append to DeployedArmy when scheduling ─────────────────────────────
    ...
    if not scout_only:
        # Deduct from garrison and add to deployed
        army = get_rows("Army")
        for key, qty in comp.items():
            # garrison deduction (as before)...
            ...
            # add to DeployedArmy
            append_row(DEPLOY_SHEET, [uid, key, str(qty)])
    ...

handler = CommandHandler("attack", attack)
