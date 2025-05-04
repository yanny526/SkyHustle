# handlers/attack.py

import time
import random
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from modules.unit_manager import UNITS
from modules.challenge_manager import load_challenges, update_player_progress


async def scout_report_job(context: ContextTypes.DEFAULT_TYPE):
    """After 5 minutes, DM the scouting report and remove the job from pending."""
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    defender_name  = data["defender_name"]
    chat_id        = int(uid)

    # Build the report
    army_rows   = get_rows("Army")
    lines       = [f"🔎 *Scouting Report: {defender_name}*"]
    total_power = 0

    for row in army_rows[1:]:
        if row[0] != defender_id:
            continue
        unit_key = row[1]
        count    = int(row[2])
        if count <= 0:
            continue
        display, emoji, tier, unit_power, _ = UNITS[unit_key]
        power = unit_power * count
        total_power += power

        lines.append(
            f"• {emoji} *{display}* (Tier {tier}) — {count} units ({power}⚔️)"
        )

    if total_power > 0:
        lines.append("")  # spacer
        lines.append(f"⚔️ *Total Power:* {total_power}⚔️")
        text = "\n".join(lines)
    else:
        text = f"🔎 No troops detected at *{defender_name}*."

    # Send the report
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )

    # Remove this job from pending list
    app = context.application
    user_chat = app.chat_data.setdefault(chat_id, {})
    pending   = user_chat.get("pending", [])
    if context.job.name in pending:
        pending.remove(context.job.name)
    user_chat["pending"] = pending


async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    """After 30 minutes, resolve combat, update sheets, DM result, and clear from pending."""
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    attacker_name  = data["attacker_name"]
    defender_name  = data["defender_name"]
    atk_i          = data["atk_i"]
    def_i          = data["def_i"]
    timestamp      = data["timestamp"]
    chat_id        = int(uid)

    # Compute power helper
    def power(urow):
        total = 0
        for r in get_rows("Army")[1:]:
            if r[0] != urow[0]:
                continue
            count     = int(r[2])
            unit_power = UNITS[r[1]][3]
            total    += count * unit_power
        return total

    players  = get_rows("Players")
    attacker = players[atk_i]
    defender = players[def_i]

    atk_roll = power(attacker) * random.uniform(0.9, 1.1)
    def_roll = power(defender) * random.uniform(0.9, 1.1)

    if atk_roll > def_roll:
        result = "win"
        spoils = max(1, int(defender[3]) // 10)
        msg = (
            f"🏆 *{attacker_name}* has *defeated* *{defender_name}*!\n"
            f"💰 *Loot:* Stole {spoils} Credits."
        )
        attacker_credits = int(attacker[3]) + spoils
        defender_credits = int(defender[3]) - spoils
    else:
        result = "loss"
        spoils = max(1, int(attacker[3]) // 20)
        msg = (
            f"💥 *{attacker_name}* was *defeated* by *{defender_name}*!\n"
            f"💸 *Loss:* Lost {spoils} Credits."
        )
        attacker_credits = int(attacker[3]) - spoils
        defender_credits = int(defender[3]) + spoils

    # Update sheets
    attacker[3], defender[3] = str(attacker_credits), str(defender_credits)
    update_row("Players", atk_i, attacker)
    update_row("Players", def_i, defender)
    append_row("CombatLog", [uid, defender_id, timestamp, result, str(spoils)])

    # DM the result
    await context.bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode=ParseMode.MARKDOWN
    )

    # Remove from pending
    app = context.application
    user_chat = app.chat_data.setdefault(chat_id, {})
    pending   = user_chat.get("pending", [])
    if context.job.name in pending:
        pending.remove(context.job.name)
    user_chat["pending"] = pending


@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <CommanderName> [-s <num_scouts>] –
    Scouts cost 1⚡ each; main attack costs 5⚡.
    """
    user        = update.effective_user
    uid         = str(user.id)
    args        = context.args.copy()
    chat_id     = update.effective_chat.id

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <CommanderName> [-s <number_of_scouts>]`",
            parse_mode=ParseMode.MARKDOWN
        )

    target      = args.pop(0)
    scout_count = 0

    # Parse scouts flag
    if "-s" in args:
        idx = args.index("-s")
        try:
            scout_count = int(args[idx + 1])
        except:
            scout_count = 1
        args.pop(idx)
        if idx < len(args):
            args.pop(idx)

    # Find players
    players = get_rows("Players")
    attacker = defender = None
    atk_i = def_i = None
    for i, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            attacker, atk_i = row.copy(), i
        if row[1].lower() == target.lower():
            defender, def_i = row.copy(), i

    if not attacker:
        return await update.message.reply_text("❗ Run /start first.", parse_mode=ParseMode.MARKDOWN)
    if not defender:
        return await update.message.reply_text(f"❌ Commander *{target}* not found.", parse_mode=ParseMode.MARKDOWN)
    if defender[0] == uid:
        return await update.message.reply_text("❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN)

    # Energy cost
    energy     = int(attacker[5])
    total_cost = 5 + scout_count
    if energy < total_cost:
        return await update.message.reply_text(f"❌ Need {total_cost}⚡, but you have {energy}⚡.", parse_mode=ParseMode.MARKDOWN)
    attacker[5] = str(energy - total_cost)
    update_row("Players", atk_i, attacker)

    # Timestamp for job names
    timestamp = str(int(time.time()))

    # Schedule jobs & record them
    pending = context.chat_data.get("pending", [])

    if scout_count > 0:
        job = context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=f"scout_{uid}_{defender[0]}_{timestamp}",
            data={"uid": uid, "defender_id": defender[0], "defender_name": defender[1]}
        )
        pending.append(job.name)

    job = context.job_queue.run_once(
        combat_resolution_job,
        when=timedelta(minutes=30),
        name=f"attack_{uid}_{defender[0]}_{timestamp}",
        data={
            "uid": uid,
            "defender_id": defender[0],
            "attacker_name": attacker[1],
            "defender_name": defender[1],
            "atk_i": atk_i,
            "def_i": def_i,
            "timestamp": timestamp
        }
    )
    pending.append(job.name)

    # Persist pending list
    context.chat_data["pending"] = pending

    # Track challenges
    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    # Confirmation UI
    lines = ["⚔️ *Your orders are set!*"]
    if scout_count > 0:
        lines.append(f"🔎 Scouts x{scout_count} (cost {scout_count}⚡) arriving in *5 minutes*.")
    lines.append(f"🏹 Main attack (cost 5⚡) on *{defender[1]}* arriving in *30 minutes*.")
    lines.append("📜 Tap below to view or refresh pending operations.")

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


handler = CommandHandler("attack", attack)
