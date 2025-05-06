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
from sheets_service import get_rows
from utils.format_utils import (
    format_bar,
    get_building_emoji,
    get_build_costs,
    section_header,
)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # ─── Retrieve Player Data ───────────────────────────────────────────────
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == uid:
            commander  = html.escape(row[1])
            credits    = int(row[3])
            minerals   = int(row[4])
            energy     = int(row[5])
            last_raw   = row[6] if len(row) > 6 else None
            last_seen  = int(last_raw) if last_raw and last_raw.isdigit() else None
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # ─── Production & Infrastructure ───────────────────────────────────────
    binfo   = get_building_info(uid)
    rates   = get_production_rates(binfo)
    health  = get_building_health(uid)
    all_bld = ["Bank"] + list(BUILDING_MAX_LEVEL.keys())

    # ─── Army Composition & Strength ────────────────────────────────────────
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

    # ─── Supply Tick Countdown ─────────────────────────────────────────────
    tick_str = ""
    if 'last_seen' in locals() and last_seen is not None:
        secs_left = max(0, (last_seen + 3600) - now.timestamp())
        m, s = divmod(int(secs_left), 60)
        tick_str = f"{m}m{s:02d}s"

    # ─── Build Status Text ─────────────────────────────────────────────────
    lines = []
    lines.append(section_header("Resources & Supplies"))
    lines.append(f"🪙 Credits   : {credits}")
    lines.append(f"⛏️ Minerals : {minerals}")
    lines.append(f"⚡ Energy   : {energy}")
    if tick_str:
        lines.append(f"⏱ Tick in   : {tick_str}")
    lines.append("")

    lines.append(section_header("Production / min"))
    lines.append(f"🪙 {rates['credits']}   ⛏️ {rates['minerals']}   ⚡ {rates['energy']}")
    lines.append("")

    lines.append(section_header("Infrastructure Status"))
    for b in all_bld:
        lvl        = binfo.get(b, 0)
        hp         = health.get(b, {"current": 0, "max": 0})
        current_hp = hp["current"]
        max_hp     = hp["max"]
        bar        = format_bar(current_hp, max_hp)
        lines.append(f"{get_building_emoji(b)} {b}: Lvl {lvl} {bar} ({current_hp}/{max_hp})")
    lines.append("")

    lines.append(section_header("Army Strength"))
    total_power = (garrison_power + deployed_power) or 1
    lines.append(f"🛡️ Garrison : {format_bar(garrison_power, total_power)} ({garrison_power})")
    lines.append(f"🚚 Deployed : {format_bar(deployed_power, total_power)} ({deployed_power})")
    lines.append("")

    lines.append(section_header("Garrison Composition"))
    if garrison:
        for key, cnt in garrison.items():
            disp, emoji, *_ = UNITS[key]
            lines.append(f"{emoji} {disp}: {cnt}")
    else:
        lines.append("None")
    lines.append("")

    lines.append(section_header("Deployed Forces"))
    if deployed:
        for key, cnt in deployed.items():
            disp, emoji, *_ = UNITS[key]
            lines.append(f"{emoji} {disp}: {cnt}")
    else:
        lines.append("None")
    lines.append("")

    lines.append(section_header("Next Upgrade Paths"))
    for b in all_bld:
        lvl = binfo.get(b, 0)
        nl  = lvl + 1
        cC, cM, eC = get_build_costs(b, nl)
        prod_info  = PRODUCTION_PER_LEVEL.get(b)
        if prod_info:
            key, per = prod_info
            gain      = per * nl - per * lvl
            gain_str  = f"+{gain} {key}/min"
        else:
            gain_str = "–"
        lines.append(
            f"{get_building_emoji(b)} {b}: {lvl}→{nl} | cost 🪙{cC}, ⛏️{cM}, ⚡{eC} | {gain_str}"
        )

    report = "\n".join(lines)
    text = (
        f"<b>🛡️⚔️ War Report: Commander {commander} ⚔️🛡️</b>\n"
        f"<pre>{html.escape(report)}</pre>"
    )

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh Report", callback_data="status")
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "status":
        return await status(update, context)

handler          = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^status$")
