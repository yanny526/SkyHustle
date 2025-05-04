# handlers/status.py

from datetime import datetime
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

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # ──────────────────────────────────────────────────────────────────────────
    # 1) Load core player data
    # ──────────────────────────────────────────────────────────────────────────
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == uid:
            name      = row[1]
            credits   = int(row[3])
            minerals  = int(row[4])
            energy    = int(row[5])
            last_seen = int(row[6]) if len(row) > 6 and row[6].isdigit() else None
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # ──────────────────────────────────────────────────────────────────────────
    # 2) Buildings & Production
    # ──────────────────────────────────────────────────────────────────────────
    binfo   = get_building_info(uid)
    rates   = get_production_rates(binfo)
    health  = get_building_health(uid)
    all_bld = ["Bank"] + list(BUILDING_MAX_LEVEL.keys())

    # ──────────────────────────────────────────────────────────────────────────
    # 3) Garrison vs Deployed Army & Power
    # ──────────────────────────────────────────────────────────────────────────
    # Garrison
    army_rows = get_rows("Army")
    garrison = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}
    garrison_power = sum(cnt * UNITS[key][3] for key, cnt in garrison.items())

    # Deployed
    dep_rows = get_rows("DeployedArmy")
    deployed = {}
    for r in dep_rows[1:]:
        if r[0] != uid: continue
        key, cnt = r[1], int(r[2])
        if cnt > 0:
            deployed[key] = deployed.get(key, 0) + cnt
    deployed_power = sum(cnt * UNITS[key][3] for key, cnt in deployed.items())

    # ──────────────────────────────────────────────────────────────────────────
    # 4) Assemble message
    # ──────────────────────────────────────────────────────────────────────────
    lines = []

    # Header
    lines.append(f"🔥⚔️ *Commander Report: {name}* ⚔️🔥")
    lines.append("")

    # Resources
    lines.append("💰 *Resources*")
    lines.append(f" • 🪙 Credits : {credits}")
    lines.append(f" • ⛏️ Minerals: {minerals}")
    lines.append(f" • ⚡ Energy  : {energy}")
    lines.append("")

    # Next tick
    if last_seen is not None:
        secs_to_next = max(0, (last_seen + 3600) - now.timestamp())
        m, s = divmod(int(secs_to_next), 60)
        lines.append(f"⏱️ Next Tick in {m}m {s}s")
        lines.append("")

    # Production rates
    lines.append("🏭 *Production/minute*")
    lines.append(f" • 🪙 {rates['credits']}   ⛏️ {rates['minerals']}   ⚡ {rates['energy']}")
    lines.append("")

    # Buildings & health
    lines.append("🏰 *Buildings & Health*")
    for b in all_bld:
        lvl = binfo.get(b, 0)
        hp  = health.get(b, {"current":0, "max":0})
        lines.append(f" • {b}: Lvl {lvl} (HP {hp['current']}/{hp['max']})")
    lines.append("")

    # Power summary
    lines.append("⚔️ *Army Strength*")
    lines.append(f" • 🛡️ Garrison : {garrison_power}⚔️")
    lines.append(f" • 🚚 Deployed : {deployed_power}⚔️")
    lines.append("")

    # Garrison details
    lines.append("🛡️ *Garrison Composition*")
    if garrison:
        for key, cnt in garrison.items():
            disp, emoji, *_ = UNITS[key]
            lines.append(f"  • {emoji} {disp}: {cnt}")
    else:
        lines.append("  • None")
    lines.append("")

    # Deployed details
    lines.append("🚚 *Deployed Forces*")
    if deployed:
        for key, cnt in deployed.items():
            disp, emoji, *_ = UNITS[key]
            lines.append(f"  • {emoji} {disp}: {cnt}")
    else:
        lines.append("  • None")
    lines.append("")

    # Next upgrade suggestions
    lines.append("🔧 *Next Upgrade Suggestions*")
    for b in all_bld:
        lvl = binfo.get(b, 0)
        nlv = lvl + 1
        c₳ = nlv * 100
        c⛏ = nlv * 50
        prod_info = PRODUCTION_PER_LEVEL.get(b)
        if prod_info:
            key, per = prod_info
            gain = per * nlv - per * lvl
            gain_s = f"+{gain} {key}/min"
        else:
            gain_s = "–"
        lines.append(f"  • {b}: {lvl}→{nlv} | cost 🪙{c₳}, ⛏️{c⛏} | {gain_s}")

    text = "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    # 5) Inline refresh
    # ──────────────────────────────────────────────────────────────────────────
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh Report", callback_data="status")
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "status":
        return await status(update, context)

handler          = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^status$")
