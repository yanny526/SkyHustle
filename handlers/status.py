from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

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

    # 1) Serve from cache if fresh
    cache = STATUS_CACHE.get(uid)
    if cache and now - cache["time"] < CACHE_TTL:
        return await update.message.reply_text(
            cache["text"],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cache["keyboard"],
        )

    # 2) Fetch player resources
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == uid:
            name = row[1]
            credits, minerals, energy = map(int, row[3:6])
            break
    else:
        return await update.message.reply_text("❗ Please run /start first.")

    # 3) Compute historical deltas
    prev = cache["resources"] if cache else {}
    deltas = {
        "credits": (credits - prev.get("credits", credits)) if "credits" in prev else None,
        "minerals": (minerals - prev.get("minerals", minerals)) if "minerals" in prev else None,
        "energy":   (energy   - prev.get("energy", energy))   if "energy"   in prev else None,
    }

    # 4) Buildings & production
    binfo = get_building_info(uid)
    rates = get_production_rates(binfo)

    # 5) Next upgrade ETA
    pending = get_pending_upgrades(uid)
    if pending:
        nxt = min(pending, key=lambda x: x["end_ts"])
        dt = timedelta(seconds=int(nxt["end_ts"] - now.timestamp()))
        eta = f"{dt.seconds//3600}h {(dt.seconds%3600)//60}m"
        upg_line = f"⚙️ Next upgrade: {nxt['bname']} → Lvl {nxt['target_lvl']} in {eta}"
    else:
        upg_line = "⚙️ No upgrades pending"

    # 6) Building health
    health = get_building_health(uid)

    # 7) Assemble message lines
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
    lines += ["", upg_line, ""]

    # 8) Army counts
    army = {r[1]: int(r[2]) for r in get_rows("Army")[1:] if r[0] == uid}
    lines.append("⚔️ *Army:*")
    for key, info in UNITS.items():
        disp, emoji, tier, _, _ = info
        cnt = army.get(key, 0)
        if cnt > 0:
            lines.append(f" • {emoji} {disp}: {cnt}")
    lines.append("")

    text = "\n".join(lines)

    # 9) Inline keyboard for quick actions
    keyboard = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("Upgrade HQ", callback_data="upgrade_HQ"),
        InlineKeyboardButton("Train Units", callback_data="train_units"),
        InlineKeyboardButton("View Army", callback_data="view_army"),
    ])

    # 10) Cache and send
    STATUS_CACHE[uid] = {
        "time": now,
        "text": text,
        "resources": {"credits": credits, "minerals": minerals, "energy": energy},
        "keyboard": keyboard,
    }

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

handler = CommandHandler("status", status)
