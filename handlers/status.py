# handlers/status.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.upgrade_manager import get_pending_upgrades
from modules.building_manager import (
    get_building_info,
    get_production_rates,
    get_building_health,
)
from modules.unit_manager import UNITS
from sheets_service import get_rows, update_row

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
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # 2) Helpers
    def render_bar(value, rate):
        length = 10
        maxv   = max(value, rate * 5, 1)
        filled = int(value / maxv * length)
        return "█" * filled + "░" * (length - filled)

    # 3) Production & buildings
    binfo  = get_building_info(uid)
    rates  = get_production_rates(binfo)
    health = get_building_health(uid)

    # 4) Upgrades in progress
    pending = get_pending_upgrades(uid)

    # 5) Army composition
    army_rows = get_rows("Army")
    counts    = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}

    # 6) Build message lines
    lines = [
        f"🏰 *Commander:* {name}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"💰 *Credits:*  {credits}   {render_bar(credits, rates['credits'])}",
        f"⛏️ *Minerals:* {minerals}   {render_bar(minerals, rates['minerals'])}",
        f"⚡ *Energy:*   {energy}   {render_bar(energy, rates['energy'])}",
        "",
        f"💹 *Production/min:* 🪙{rates['credits']}   ⛏️{rates['minerals']}   ⚡{rates['energy']}",
        "",
        "⏳ *Upgrades In Progress:*"
    ]

    if pending:
        for upg in sorted(pending, key=lambda u: u["end_ts"]):
            rem = int(upg["end_ts"] - now.timestamp())
            hrs, rem2 = divmod(rem, 3600)
            mins, _   = divmod(rem2, 60)
            lines.append(f"   🔨 {upg['bname']} → Lvl {upg['target_lvl']} in {hrs}h {mins}m")
    else:
        lines.append("   ✅ None")

    lines += [
        "",
        "🏗️ *Buildings & Health:*"
    ]
    for btype, lvl in binfo.items():
        cur = health.get(btype, {}).get("current", 0)
        mx  = health.get(btype, {}).get("max", 0)
        lines.append(f"   🏢 {btype}: Lvl {lvl} (HP {cur}/{mx})")

    lines += [
        "",
        "⚔️ *Army Composition:*"
    ]
    for key, (disp, emoji, *_) in UNITS.items():
        cnt = counts.get(key, 0)
        if cnt > 0:
            lines.append(f"   {emoji} {disp}: {cnt}")

    text = "\n".join(lines)

    # 7) Only a Refresh button
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="status")
    )

    # 8) Send or edit
    if update.message:
        sent = await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        sent = await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        await update.callback_query.answer()

    # 9) Quest progression (check–and–reward)
    header = players[0]
    for idx, prow in enumerate(players[1:], start=1):
        if prow[0] == uid:
            while len(prow) < len(header):
                prow.append("")
            progress = prow[7]
            break
    else:
        return

    if progress == "step3":
        # Grant reward and advance
        prow[3]  = str(int(prow[3]) + 300)
        prow[7]  = "step4"
        update_row("Players", idx, prow)
        await context.bot.send_message(
            chat_id=sent.chat.id,
            text=(
                "🎉 *Mission Update!*\n"
                "✅ You checked your status!\n"
                "💳 +300 Credits awarded!\n\n"
                "Next mission: `/attack <CommanderName>`"
            ),
            parse_mode=ParseMode.MARKDOWN
        )

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 🔄 Refresh button."""
    if update.callback_query.data == "status":
        return await status(update, context)

# Export handlers
handler = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button, pattern="^status$")
