# handlers/status.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.building_manager import (
    get_building_info,
    get_production_rates,
    get_building_health,
)
from modules.unit_manager import UNITS
from modules.upgrade_manager import get_pending_upgrades
from sheets_service import get_rows

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # 1) Load player record
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == uid:
            name     = row[1]
            credits  = int(row[3])
            minerals = int(row[4])
            energy   = int(row[5])
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # 2) Production & buildings
    binfo   = get_building_info(uid)
    rates   = get_production_rates(binfo)
    health  = get_building_health(uid)

    # 3) Army composition
    army_rows = get_rows("Army")
    counts    = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}

    # 4) Build message lines
    lines = [
        f"🏰 *Commander:* {name}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"💰 *Credits:*  {credits}",
        f"⛏️ *Minerals:* {minerals}",
        f"⚡ *Energy:*   {energy}",
        "",
        f"💹 *Production/min:* 🪙{rates['credits']}   ⛏️{rates['minerals']}   ⚡{rates['energy']}",
        "",
        "🔧 *Next Upgrade Suggestions:*"
    ]

    # Next-upgrade info
    pending = get_pending_upgrades(uid)
    for btype, lvl in binfo.items():
        next_lvl      = lvl + 1
        cost_credits  = next_lvl * 100      # adjust to real formula
        cost_minerals = next_lvl * 50       # adjust as needed
        inc_credit    = int(rates['credits'] * 0.1)
        inc_mineral   = int(rates['minerals'] * 0.1)
        inc_energy    = int(rates['energy'] * 0.1)
        lines.append(
            f"   • {btype}: {lvl}→{next_lvl} | cost 🪙{cost_credits}, ⛏️{cost_minerals} | "
            f"+🪙{inc_credit}/m, +⛏️{inc_mineral}/m, +⚡{inc_energy}/m"
        )

    lines += [
        "",
        "🏗️ *Buildings & Health:*"
    ]
    for btype, lvl in binfo.items():
        cur = health.get(btype, {}).get("current", 0)
        mx  = health.get(btype, {}).get("max", 0)
        lines.append(f"   • {btype}: Lvl {lvl} (HP {cur}/{mx})")

    lines += [
        "",
        "⚔️ *Army Composition:*"
    ]
    for key, (disp, emoji, *_ ) in UNITS.items():
        cnt = counts.get(key, 0)
        if cnt > 0:
            lines.append(f"   • {emoji} {disp}: {cnt}")

    text = "\n".join(lines)

    # 5) Only a Refresh button
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="status")
    )

    # 6) Send or edit
    if update.message:
        sent = await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )
    else:
        await update.callback_query.answer()
        sent = await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 🔄 Refresh button."""
    if update.callback_query.data == "status":
        return await status(update, context)

# Export handlers
handler = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^status$")
