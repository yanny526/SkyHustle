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
    """After 5 minutes, DM the scouting report and remove from pending."""
    data          = context.job.data
    uid           = data["uid"]
    defender_id   = data["defender_id"]
    defender_name = data["defender_name"]
    chat_id       = int(uid)

    # Build the report from full Army sheet
    army_rows   = get_rows("Army")
    lines       = [f"🔎 *Scouting Report: {defender_name}*"]
    total_power = 0
    for row in army_rows[1:]:
        if row[0] != defender_id: continue
        key, count = row[1], int(row[2])
        if count <= 0: continue
        disp, emoji, tier, power, _ = UNITS[key]
        unit_power = power * count
        total_power += unit_power
        lines.append(f"• {emoji} *{disp}* (Tier {tier}) — {count} pcs ({unit_power}⚔️)")
    if total_power:
        lines.append(f"\n⚔️ *Total Power:* {total_power}⚔️")
        text = "\n".join(lines)
    else:
        text = f"🔎 No troops detected at *{defender_name}*."

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

    # remove from pending
    user_chat = context.chat_data.setdefault(chat_id, {})
    pending   = user_chat.get("pending", [])
    if context.job.name in pending:
        pending.remove(context.job.name)
    user_chat["pending"] = pending

async def combat_resolution_job(context: ContextTypes.DEFAULT_TYPE):
    """After 30 minutes, resolve combat using the saved composition."""
    data           = context.job.data
    uid            = data["uid"]
    defender_id    = data["defender_id"]
    attacker_name  = data["attacker_name"]
    defender_name  = data["defender_name"]
    atk_i          = data["atk_i"]
    def_i          = data["def_i"]
    timestamp      = data["timestamp"]
    composition    = data["composition"]  # our chosen detachment
    chat_id        = int(uid)

    # compute power of a given detachment
    def detachment_power(comp):
        return sum(count * UNITS[key][3] for key, count in comp.items())

    atk_power = detachment_power(composition) * random.uniform(0.9, 1.1)

    # defender uses their full current army
    players = get_rows("Players")
    defender_row = players[def_i]
    # build defender composition from sheet
    def_comp = {
        row[1]: int(row[2])
        for row in get_rows("Army")[1:]
        if row[0] == defender_id
    }
    def_power = detachment_power(def_comp) * random.uniform(0.9, 1.1)

    if atk_power > def_power:
        result = "win"
        spoils = max(1, int(defender_row[3]) // 10)
        msg = (
            f"🏆 *{attacker_name}* defeated *{defender_name}*!\n"
            f"💰 *Loot:* Stole {spoils} Credits."
        )
        attacker_credits = int(players[atk_i][3]) + spoils
        defender_credits = int(defender_row[3]) - spoils
    else:
        result = "loss"
        spoils = max(1, int(players[atk_i][3]) // 20)
        msg = (
            f"💥 *{attacker_name}* was defeated by *{defender_name}*!\n"
            f"💸 *Loss:* Lost {spoils} Credits."
        )
        attacker_credits = int(players[atk_i][3]) - spoils
        defender_credits = int(defender_row[3]) + spoils

    # update resources
    players[atk_i][3] = str(attacker_credits)
    update_row("Players", atk_i, players[atk_i])
    players[def_i][3] = str(defender_credits)
    update_row("Players", def_i, players[def_i])

    append_row("CombatLog", [uid, defender_id, timestamp, result, str(spoils)])

    # DM result
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

    # remove from pending
    user_chat = context.chat_data.setdefault(chat_id, {})
    pending   = user_chat.get("pending", [])
    if context.job.name in pending:
        pending.remove(context.job.name)
    user_chat["pending"] = pending

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack <CommanderName> -u infantry:20 tanks:5 ... [-s scouts]
    Scouts cost 1⚡ each; main attack 5⚡.
    """
    user = update.effective_user
    uid  = str(user.id)
    args = context.args.copy()
    chat_id = update.effective_chat.id

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/attack <CommanderName> -u infantry:10 tanks:5 ... [-s <num>]`",
            parse_mode=ParseMode.MARKDOWN
        )

    # target
    target = args.pop(0)

    # parse scouts
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

    # parse units
    comp = {}
    if "-u" in args:
        i = args.index("-u")
        raw = []
        # collect all tokens after -u until next flag
        for tok in args[i+1:]:
            if tok.startswith("-"):
                break
            raw.append(tok)
        # remove parsed
        args = args[:i] + [t for t in args[i+1+len(raw):]]
        # build composition dict
        for pair in raw:
            if ":" in pair:
                key, qty = pair.split(":", 1)
                if key in UNITS and qty.isdigit():
                    comp[key] = int(qty)
    # default: send all if none specified
    army_rows = get_rows("Army")
    if not comp:
        for row in army_rows[1:]:
            if row[0] == uid:
                comp[row[1]] = int(row[2])

    # find players & indices
    players = get_rows("Players")
    attacker = defender = None
    atk_i = def_i = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            attacker, atk_i = row.copy(), idx
        if row[1].lower() == target.lower():
            defender, def_i = row.copy(), idx

    if not attacker:
        return await update.message.reply_text("❗ Run /start first.", parse_mode=ParseMode.MARKDOWN)
    if not defender:
        return await update.message.reply_text(f"❌ Commander *{target}* not found.", parse_mode=ParseMode.MARKDOWN)
    if defender[0] == uid:
        return await update.message.reply_text("❌ You cannot attack yourself!", parse_mode=ParseMode.MARKDOWN)

    # compute total cost & energy
    energy = int(attacker[5])
    cost   = 5 + scout_count
    if energy < cost:
        return await update.message.reply_text(f"❌ Need {cost}⚡ but have {energy}⚡.", parse_mode=ParseMode.MARKDOWN)
    attacker[5] = str(energy - cost)
    update_row("Players", atk_i, attacker)

    # deduct units up front
    for unit_key, qty in comp.items():
        for i, arow in enumerate(army_rows[1:], start=1):
            if arow[0] == uid and arow[1] == unit_key:
                new_count = max(0, int(arow[2]) - qty)
                arow[2] = str(new_count)
                update_row("Army", i, arow)
                break

    # timestamp & schedule
    ts = str(int(time.time()))
    pending = context.chat_data.get("pending", [])

    if scout_count > 0:
        j = context.job_queue.run_once(
            scout_report_job,
            when=timedelta(minutes=5),
            name=f"scout_{uid}_{defender[0]}_{ts}",
            data={"uid": uid, "defender_id": defender[0], "defender_name": defender[1]}
        )
        pending.append(j.name)

    j = context.job_queue.run_once(
        combat_resolution_job,
        when=timedelta(minutes=30),
        name=f"attack_{uid}_{defender[0]}_{ts}",
        data={
            "uid": uid,
            "defender_id": defender[0],
            "attacker_name": attacker[1],
            "defender_name": defender[1],
            "atk_i": atk_i,
            "def_i": def_i,
            "timestamp": ts,
            "composition": comp
        }
    )
    pending.append(j.name)

    context.chat_data["pending"] = pending

    # track challenges
    for ch in load_challenges("daily"):
        if ch.key == "attacks":
            update_player_progress(uid, ch)
            break

    # build UI summary
    parts = []
    if comp:
        parts.append("• " + "  ".join(f"{UNITS[k][1]}×{v}" for k, v in comp.items()))
    if scout_count:
        parts.append(f"• 🔎 Scouts×{scout_count} (1⚡ each)")
    ui = (
        "⚔️ *Your orders are set!* \n\n"
        f"🏹 Attack on *{defender[1]}* in *30 minutes*\n"
        + ("\n".join(parts)) +
        f"\n\n📝 You’ll get the scout & battle reports here."
    )

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(ui, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

handler = CommandHandler("attack", attack)
