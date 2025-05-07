# handlers/status.py

from datetime import datetime
import html

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from config import BUILDING_MAX_LEVEL
from modules.building_manager import (
    PRODUCTION_PER_LEVEL,
    get_building_info,
    get_production_rates,
    get_building_health,
)
from modules.unit_manager import UNITS
from sheets_service import get_rows, update_row
from utils.format_utils import (
    format_bar,
    get_building_emoji,
    get_build_costs,
    section_header,
)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # Retrieve Player Data
    players = get_rows("Players")
    commander = "Unknown Commander"
    credits = 0
    minerals = 0
    energy = 0
    premium_credits = 0
    last_login = "N/A"
    for row in players[1:]:
        if row[0] == uid:
            commander = html.escape(row[1] or "Unknown Commander")
            try:
                credits = int(row[3])
            except:
                credits = 0
            try:
                minerals = int(row[4])
            except:
                minerals = 0
            try:
                energy = int(row[5])
            except:
                energy = 0
            try:
                premium_credits = int(row[7]) if len(row) > 7 else 0
            except:
                premium_credits = 0
            if len(row) > 6 and row[6]:
                last_login = datetime.fromtimestamp(int(row[6])).strftime('%Y-%m-%d %H:%M')
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # Production & Infrastructure
    binfo = get_building_info(uid)
    rates = get_production_rates(binfo)
    health = get_building_health(uid)
    all_bld = ["Bank"] + list(BUILDING_MAX_LEVEL.keys())

    # Army Composition & Strength
    army_rows = get_rows("Army")
    garrison = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}
    garrison_power = sum(cnt * UNITS[key][3] for key, cnt in garrison.items())

    dep_rows = get_rows("DeployedArmy")
    deployed = {}
    for r in dep_rows[1:]:
        if r[0] != uid:
            continue
        key, cnt = r[1], int(r[2])
        if cnt > 0:
            deployed[key] = deployed.get(key, 0) + cnt
    deployed_power = sum(cnt * UNITS[key][3] for key, cnt in deployed.items())

    # Supply Tick Countdown
    tick_str = ""

    # Build Status Text
    lines = []
    lines.append(section_header("WAR ROOM BRIEFING", "🏰", color="gold"))
    lines.append(f"  Commander: [{commander}]")
    lines.append(f"  Last Login: [{last_login}]")
    lines.append("")

    lines.append(section_header("RESOURCES", "💰", color="green"))
    lines.append(f"  Credits:  [{credits}]")
    lines.append(f"  Minerals: [{minerals}]")
    lines.append(f"  Energy:   [{energy}]")
    lines.append(f"  Premium Credits: [{premium_credits}] ⭐")  # New premium currency display
    lines.append("")

    lines.append(section_header("PRODUCTION RATES", "⚙️", color="blue"))
    lines.append(f"  Credits: [{rates['credits']}/min]")
    lines.append(f"  Minerals: [{rates['minerals']}/min]")
    lines.append(f"  Energy:   [{rates['energy']}/min]")
    lines.append("")

    lines.append(section_header("INFRASTRUCTURE STATUS", "🏭", color="magenta"))
    for b in all_bld:
        lvl = binfo.get(b, 0)
        hp = health.get(b, {"current": 0, "max": 0})
        current_hp = hp["current"]
        max_hp = hp["max"]
        bar = format_bar(current_hp, max_hp)
        lines.append(f"{get_building_emoji(b)} {b}: Lvl {lvl} {bar} ({current_hp}/{max_hp})")
    lines.append("")

    lines.append(section_header("ARMY STRENGTH", "⚔️", color="red"))
    total_power = garrison_power + deployed_power or 1
    lines.append(f"🛡️ Garrison : {format_bar(garrison_power, total_power)} ({garrison_power})")
    lines.append(f"🚚 Deployed : {format_bar(deployed_power, total_power)} ({deployed_power})")
    lines.append("")

    lines.append(section_header("NEXT UPGRADE PATHS", "➡️", color="cyan"))
    for b in all_bld:
        lvl = binfo.get(b, 0)
        nl = lvl + 1
        cC, cM, eC = get_build_costs(b, nl)
        prod_info = PRODUCTION_PER_LEVEL.get(b)
        if prod_info:
            key, per = prod_info
            gain = per * nl - per * lvl
            gain_str = f"+{gain} {key}/min"
        else:
            gain_str = "–"
        lines.append(
            f"{get_building_emoji(b)} {b}: {lvl}→{nl} | cost 💳{cC}, ⛏️{cM}, ⚡{eC} | {gain_str}"
        )

    lines.append(section_header("AVAILABLE ABILITIES", "✨", color="purple"))
    lines.append("Use `/ability` to see special abilities for your units")
    lines.append("Premium members can purchase abilities to enhance their units in battle!")

    report = "\n".join(lines)
    text = (
        f"<b>⚔️🏰 WAR ROOM BRIEFING: Commander {commander} 🏰⚔️</b>\n"
        f"<pre>{html.escape(report)}</pre>"
    )

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="status")]])

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb
        )

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "status":
        return await status(update, context)

handler = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^(status)$")
