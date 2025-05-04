# handlers/status.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from config import BUILDING_MAX_LEVEL
from modules.building_manager import PRODUCTION_PER_LEVEL, get_building_info, get_production_rates, get_building_health
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
            name      = row[1]
            credits   = int(row[3])
            minerals  = int(row[4])
            energy    = int(row[5])
            # last_seen timestamp for next-tick calc, if present
            last_seen = None
            if len(row) > 6 and row[6].isdigit():
                last_seen = int(row[6])
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # 2) Production & buildings data
    binfo  = get_building_info(uid)      # {building: level}
    rates  = get_production_rates(binfo) # {'credits': x, 'minerals': y, 'energy': z}
    health = get_building_health(uid)    # {building: {'current': c, 'max': m}}

    # 3) Army composition
    army_rows = get_rows("Army")
    counts    = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}

    # 4) Determine all buildings
    all_buildings = ["Bank"] + list(BUILDING_MAX_LEVEL.keys())

    # 5) Build the status message
    lines = [
        f"🏰 *Commander:* {name}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"💰 *Credits:*  {credits}",
        f"⛏️ *Minerals:* {minerals}",
        f"⚡ *Energy:*   {energy}",
        ""
    ]

    # 6) Time to next resource "tick" (hourly)
    if last_seen is not None:
        secs_to_next = max(0, (last_seen + 3600) - now.timestamp())
        mins, secs   = divmod(int(secs_to_next), 60)
        lines.append(f"⏱️ Next resource update in {mins}m {secs}s")
        lines.append("")

    lines += [
        f"💹 *Current Production/min:* 🪙{rates['credits']}   ⛏️{rates['minerals']}   ⚡{rates['energy']}",
        "",
        "🔧 *Next Upgrade Suggestions:*"
    ]

    # 7) For each building: next level, cost, and benefit
    for btype in all_buildings:
        lvl = binfo.get(btype, 0)
        next_lvl = lvl + 1
        # cost formula (replace with your real formula if different)
        cost_credits  = next_lvl * 100
        cost_minerals = next_lvl * 50
        # benefit: for production buildings use PRODUCTION_PER_LEVEL
        prod_info = PRODUCTION_PER_LEVEL.get(btype)
        if prod_info:
            key, per_level = prod_info
            current_rate = per_level * lvl
            next_rate    = per_level * next_lvl
            benefit = next_rate - current_rate
            benefit_str = f"+{benefit} {key}/min"
        else:
            benefit_str = "–"
        lines.append(
            f"   • {btype}: {lvl}→{next_lvl} | cost 🪙{cost_credits}, ⛏️{cost_minerals} | {benefit_str}"
        )

    lines += [
        "",
        "🏗️ *Buildings & Health:*"
    ]
    # 8) List every building's current level and HP
    for btype in all_buildings:
        lvl = binfo.get(btype, 0)
        hp  = health.get(btype, {})
        cur = hp.get("current", 0)
        mx  = hp.get("max", 0)
        lines.append(f"   • {btype}: Lvl {lvl} (HP {cur}/{mx})")

    lines += [
        "",
        "⚔️ *Army Composition:*"
    ]
    # 9) Army counts
    for key, (disp, emoji, *_) in UNITS.items():
        cnt = counts.get(key, 0)
        if cnt > 0:
            lines.append(f"   • {emoji} {disp}: {cnt}")

    text = "\n".join(lines)

    # 10) Only a Refresh button
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="status")
    )

    # 11) Send or update the message
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 🔄 Refresh button."""
    if update.callback_query.data == "status":
        return await status(update, context)

# Export handlers
handler = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^status$")
