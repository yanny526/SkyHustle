from datetime import datetime
import html
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.building_manager import (
    get_build_defs,
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

from handlers.queue import queue

logger = logging.getLogger(__name__)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # ── Player & tutorial logic (unchanged) ──────────────────────────────────
    players = get_rows("Players")
    if not players:
        return await update.message.reply_text("❗ Please run /start first.")
    header = players[0]
    prog_idx = header.index("progress") if "progress" in header else None

    player_row = None
    row_index  = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            player_row = row.copy()
            row_index  = idx
            break
    if not player_row:
        return await update.message.reply_text("❗ Please run /start first.")

    if prog_idx is not None and len(player_row) > prog_idx and player_row[prog_idx] == "4":
        player_row[prog_idx] = "5"
        try:
            update_row("Players", row_index, player_row)
        except Exception as e:
            logger.error("TutorialComplete: failed to update progress: %s", e)
        text = "\n".join([
            section_header("🎉 Tutorial Complete! 🎉", pad_char="=", pad_count=3),
            "",
            "Congratulations, Commander! You’ve mastered the basics.",
            "Use `/help` to explore all features and start conquering.",
        ])
        if update.message:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # ── Core data ────────────────────────────────────────────────────────────
    for row in players[1:]:
        if row[0] == uid:
            commander  = html.escape(row[1] or "Unknown")
            credits    = int(row[3] or 0)
            minerals   = int(row[4] or 0)
            energy     = int(row[5] or 0)
            last_raw   = row[6] if len(row) > 6 else None
            last_seen  = int(last_raw) if last_raw and last_raw.isdigit() else None
            break

    # ── Buildings & Production ← now driven by your defs + CompletedBuilds ──
    defs   = get_build_defs()
    binfo  = get_building_info(uid)
    rates  = get_production_rates(binfo)
    health = get_building_health(uid)

    # order by tier, then key
    all_bld = sorted(defs.keys(), key=lambda k: (defs[k]["tier"], k))

    # ── Army sections unchanged ───────────────────────────────────────────────
    army_rows    = get_rows("Army")
    garrison     = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}
    garrison_pwr = sum(cnt * UNITS[k][3] for k, cnt in garrison.items())
    dep_rows     = get_rows("DeployedArmy")
    deployed     = {}
    for r in dep_rows[1:]:
        if r[0] == uid:
            deployed[r[1]] = deployed.get(r[1], 0) + int(r[2])
    deployed_pwr = sum(cnt * UNITS[k][3] for k, cnt in deployed.items())

    # ── Tick countdown (unchanged) ──────────────────────────────────────────
    tick_str = ""
    if last_seen is not None:
        secs_left = max(0, (last_seen + 3600) - now.timestamp())
        m, s      = divmod(int(secs_left), 60)
        tick_str  = f"{m}m{s:02d}s"

    # ── Build the report ─────────────────────────────────────────────────────
    lines = [
        section_header("Resources & Supplies"),
        f"💳 Credits   : {credits}",
        f"⛏️ Minerals : {minerals}",
        f"⚡ Energy   : {energy}",
    ]
    if tick_str:
        lines.append(f"⏱ Tick in   : {tick_str}")

    lines += [
        "",
        section_header("Production / min"),
        f"💳 {rates['credits']}   ⛏️ {rates['minerals']}   ⚡ {rates['energy']}",
        "",
        section_header("Infrastructure Status")
    ]

    for b in all_bld:
        lvl = binfo.get(b, 0)
        hp  = health.get(b, {"current": 0, "max": 0})
        bar = format_bar(hp["current"], hp["max"])
        # use defs[b]['name'] for display
        lines.append(f"{get_building_emoji(b)} {defs[b]['name']}: Lvl {lvl} {bar} ({hp['current']}/{hp['max']})")

    lines += [
        "",
        section_header("Army Strength"),
        f"🛡️ Garrison : {format_bar(garrison_pwr, garrison_pwr + deployed_pwr or 1)} ({garrison_pwr})",
        f"🚚 Deployed : {format_bar(deployed_pwr, garrison_pwr + deployed_pwr or 1)} ({deployed_pwr})",
        "",
        section_header("Next Upgrade Paths")
    ]

    for b in all_bld:
        lvl = binfo.get(b, 0)
        nl  = lvl + 1
        cC, cM, eC = get_build_costs(b, nl)
        prod_info  = PRODUCTION_PER_LEVEL.get(b)
        gain_str   = (
            f"+{prod_info[1]*nl - prod_info[1]*lvl} {prod_info[0]}/min"
            if prod_info else "–"
        )
        lines.append(
            f"{get_building_emoji(b)} {defs[b]['name']}: {lvl}→{nl} | cost 💳{cC}, ⛏️{cM}, ⚡{eC} | {gain_str}"
        )

    report = "\n".join(lines)
    status_text = (
        f"<b>⚔️🏰 WAR ROOM BRIEFING: Commander {commander} 🏰⚔️</b>\n"
        f"<pre>{html.escape(report)}</pre>"
    )

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Refresh", callback_data="status"),
        InlineKeyboardButton("🏗️ Build",    callback_data="build"),
        InlineKeyboardButton("⏳ Queue",    callback_data="queue"),
    ]])

    if update.message:
        await update.message.reply_text(status_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                status_text, parse_mode=ParseMode.HTML, reply_markup=kb
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    await q.answer()
    if data == "status":
        return await status(update, context)
    if data == "queue":
        return await queue(update, context)
    if data == "build":
        help_text = (
            "❗ Usage: `/build <building>`\n"
            "Valid: " + ", ".join(all_bld).lower()
        )
        return await q.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

handler          = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^(status|build|queue)$")
