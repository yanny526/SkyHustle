# handlers/status.py

from datetime import datetime, timedelta
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
from sheets_service import get_rows

# In-memory cache to throttle Sheets calls
STATUS_CACHE: dict = {}
CACHE_TTL = timedelta(seconds=30)

def render_bar(current: int, maximum: int, length: int = 10) -> str:
    if maximum <= 0:
        return ""
    filled = int(current / maximum * length)
    return "▇" * filled + "▁" * (length - filled)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.utcnow()

    # 1) Cached?
    cache = STATUS_CACHE.get(uid)
    if cache and now - cache["time"] < CACHE_TTL:
        return await update.message.reply_text(
            cache["text"],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cache["keyboard"],
        )

    # 2) Load resources
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == uid:
            name = row[1]
            credits, minerals, energy = map(int, row[3:6])
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # 3) Deltas
    prev = cache["resources"] if cache else {}
    deltas = {
        "credits":  (credits  - prev.get("credits",  credits))  if "credits"  in prev else None,
        "minerals": (minerals - prev.get("minerals", minerals)) if "minerals" in prev else None,
        "energy":   (energy   - prev.get("energy",   energy))   if "energy"   in prev else None,
    }

    # 4) Buildings + rates + health
    binfo  = get_building_info(uid)
    rates  = get_production_rates(binfo)
    health = get_building_health(uid)

    # 5) Assemble lines
    lines = [
        f"🏰 *Status for {name}*",
        "",
        f"💳 Credits: {credits}" + (f" ({deltas['credits']:+d})" if deltas["credits"] is not None else ""),
        f"▸ {render_bar(credits, max(credits, rates['credits'] * 5))}",
        f"⛏️ Minerals: {minerals}" + (f" ({deltas['minerals']:+d})" if deltas["minerals"] is not None else ""),
        f"▸ {render_bar(minerals, max(minerals, rates['minerals'] * 5))}",
        f"⚡ Energy: {energy}" + (f" ({deltas['energy']:+d})" if deltas["energy"] is not None else ""),
        f"▸ {render_bar(energy, max(energy, rates['energy'] * 5))}",
        "",
        f"💹 *Production/min:* Credits {rates['credits']}, Minerals {rates['minerals']}, Energy {rates['energy']}",
        "",
        "🏗️ *Buildings:*",
    ]
    for btype, lvl in binfo.items():
        line = f" • {btype}: Lvl {lvl}"
        if btype in health:
            cur, mx = health[btype]["current"], health[btype]["max"]
            line += f" (HP {cur}/{mx})"
        lines.append(line)

    # 6) Upgrades in progress
    pending = get_pending_upgrades(uid)
    lines += ["", "⏳ *Upgrades in Progress:*"]
    if pending:
        for upg in sorted(pending, key=lambda x: x["end_ts"]):
            rem = int(upg["end_ts"] - now.timestamp())
            hrs, rem2 = divmod(rem, 3600)
            mins, secs = divmod(rem2, 60)
            rem_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            lines.append(f" • {upg['bname']} → Lvl {upg['target_lvl']} ({rem_str} remaining)")
    else:
        lines.append(" • None")

    # 7) Army
    army_rows = get_rows("Army")
    counts    = {r[1]: int(r[2]) for r in army_rows[1:] if r[0] == uid}
    lines   += ["", "⚔️ *Army:*"]
    for key, info in UNITS.items():
        disp, emoji, *_ = info
        cnt = counts.get(key, 0)
        if cnt > 0:
            lines.append(f" • {emoji} {disp}: {cnt}")

    text = "\n".join(lines)

    # 8) Inline keyboard
    keyboard = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("Upgrade HQ", callback_data="upgrade_HQ"),
        InlineKeyboardButton("Train Units", callback_data="train_units"),
        InlineKeyboardButton("View Army", callback_data="view_army"),
    ])

    # 9) Cache & send
    STATUS_CACHE[uid] = {
        "time":      now,
        "text":      text,
        "resources": {"credits": credits, "minerals": minerals, "energy": energy},
        "keyboard":  keyboard,
    }
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button presses from the /status inline keyboard.
    We simply re-send the matching slash-command so your existing handlers run.
    """
    query = update.callback_query
    await query.answer()

    mapping = {
        "upgrade_HQ":   "/build",
        "train_units":  "/train",
        "view_army":    "/army",
    }
    cmd = mapping.get(query.data)
    if cmd:
        await context.bot.send_message(chat_id=query.message.chat_id, text=cmd)

# Export both the command and the callback handlers
handler        = CommandHandler("status", status)
callback_handler = CallbackQueryHandler(status_button,
                                        pattern="^(upgrade_HQ|train_units|view_army)$")
