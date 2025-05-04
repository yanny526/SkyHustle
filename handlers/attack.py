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
    """Job: send scouting report after 5 minutes."""
    data = context.job.data
    uid           = data["uid"]
    defender_id   = data["defender_id"]
    defender_name = data["defender_name"]

    # Build report
    army_rows = get_rows("Army")
    lines = [f"🔎 *Scouting Report on {defender_name}*"]
    for row in army_rows[1:]:
        if row[0] != defender_id:
            continue
        unit_key, count = row[1], int(row[2])
        if count > 0:
            emoji = UNITS[unit_key][1]
            lines.append(f"• {emoji} {unit_key}: {count}")

    text = "\n".join(lines) if len(lines) > 1 else f"🔎 No troops detected at *{defender_name}*."
    await context.bot.send_message(
        chat_id=int(uid),
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    """Job: resolve the main attack after 30 minutes."""
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    attacker_name  = data["attacker_name"]
    defender_name  = data["defender_name"]
    atk_i          = data["atk_i"]
    def_i          = data["def_i"]
    timestamp      = data["timestamp"]

    # Helper: compute army power
    def power(urow):
        total = 0
        for r in get_rows("Army")[1:]:
            if r[0] != urow[0]:
                continue
            _, unit_key, count = r
            count = int(count)
            unit_power = UNITS[unit_key][3]
            total += count * unit_power
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

    # Update sheet
    attacker[3], defender[3] = str(attacker_credits), str(defender_credits)
    update_row("Players", atk_i, attacker)
    update_row("Players", def_i, defender)
    append_row("CombatLog", [uid, defender_id, timestamp, result, str(spoils)])

    # Notify attacker
    await context.bot.send_message(
        chat_id=int(uid),
        text=msg,
        parse_mode=ParseMode.MARKDOWN
    )

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <CommanderName> [-s <count>] – 
    Dispatch scouts (-s) and launch a main assault (30 min march).
    """
    user = update.effective_user
    uid  = str(user.id)
    args = context.args

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <CommanderName> [-s <number_of_scouts>]`",
            parse_mode=ParseMode.MARKDOWN
        )

    target = args[0]
    scout_count = 0

    # Parse optional -s flag for scouts
    if "-s" in args:
        try:
            idx = args.index("-s")
            scout_count = int(args[idx + 1])
            # remove the flag from args
            args.pop(idx + 1)
            args.pop(idx)
        except (ValueError, IndexError):
            scout_count = 1

    # Find attacker & defender
    players = get_rows("Players")
    attacker = defender = None
    atk_i = def_i = None
    for i, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            attacker, atk_i = row.copy(), i
        if row[1].lower() == target.lower():
            defender, def_i = row.copy(), i

    if not attacker:
        return await update.message.reply_text("❗ Please run /start first.", parse_mode=ParseMode.MARKDOWN)
    if not defender:
        return await update.message.reply_text(
            f"❌ Commander *{target}* not found.", parse_mode=ParseMode.MARKDOWN
        )
    if defender[0] == uid:
        return await update.message.reply_text("❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN)

    # Deduct energy cost
    energy = int(attacker[5])
    if energy < 5:
        return await update.message.reply_text("❌ Not enough energy. Need 5⚡.", parse_mode=ParseMode.MARKDOWN)
    attacker[5] = str(energy - 5)
    update_row("Players", atk_i, attacker)

    # Timestamp for logs & job names
    timestamp = str(int(time.time()))

    # Schedule scout job (5 min)
    if scout_count > 0:
        context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=f"scout_{uid}_{defender[0]}_{timestamp}",
            data={"uid": uid, "defender_id": defender[0], "defender_name": defender[1]}
        )

    # Schedule combat resolution (30 min)
    context.job_queue.run_once(
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

    # Track daily attacks challenge
    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    # Confirmation UI
    lines = ["⚔️ *Your orders are set!*"]
    if scout_count > 0:
        lines.append(f"🔎 Scouts x{scout_count} arriving in *5 minutes*.")
    lines.append(f"🏹 Main attack on *{defender[1]}* arriving in *30 minutes*.")
    lines.append("📝 You’ll receive reports here when they arrive.")

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("attack", attack)
