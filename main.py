# SkyHustle - Up to Phase 9 (full Black Market system)
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os, json

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "drone", "tank"]
missions = {}
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (level 1) (one-use)"},
    "infinityscout2": {"type": "perishable", "desc": "Advanced scout (level 2) (one-use, stronger)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings (excludes Black Market units)"},
    "hazmat": {"type": "passive", "desc": "Grants access to Radiation Zones"},
}
bm_prices = {
    "infinityscout1": 200,
    "infinityscout2": 400,
    "reviveall": 500,
    "hazmat": 300
}
bm_unlock_price = 150

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(),
        "items": {},
        "blackmarket_unlocked": False
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

def find_by_name(name):
    for cid, p in players.items():
        if p["name"].lower() == name.lower():
            return cid, p
    return None, None

def give_item(p, item_id):
    p["items"].setdefault(item_id, 0)
    p["items"][item_id] += 1

def use_item(p, item_id):
    if item_id not in item_defs:
        return False, "❌ Invalid item."
    if p["items"].get(item_id, 0) <= 0:
        return False, "❌ You don't own this item."
    if item_defs[item_id]["type"] == "perishable":
        p["items"][item_id] -= 1
        if p["items"][item_id] == 0:
            del p["items"][item_id]
    return True, f"✅ Used item: {item_id}"

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        return await update.message.reply_text("🌌 SkyHustle launched! Use ,name to begin.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("Usage: ,name <alias>")
        ocid, _ = find_by_name(alias)
        if ocid and ocid != cid: return await update.message.reply_text("Alias taken.")
        p["name"] = alias
        return await update.message.reply_text(f"🚩 Callsign set to {alias}.")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        items_owned = ", ".join([f"{k} x{v}" for k,v in p["items"].items()]) or "None"
        return await update.message.reply_text(
            f"📊 {p['name'] or 'Commander'} Status:\n"
            f"🪨 Ore: {p['ore']}  ⚡ Energy: {p['energy']}  💳 Credits: {p['credits']}\n"
            f"🏭 Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\n"
            f"🤖 Army: {p['army']}\n"
            f"🎯 Items: {items_owned}\n"
            f"🛡 Shield: {shield}\n"
            f"🔓 Black Market: {'Unlocked' if p['blackmarket_unlocked'] else 'Locked'}")

    if text.startswith(",daily"):
        if p["last_daily"] == today:
            return await update.message.reply_text("🎁 Already claimed today.")
        p["credits"] += 50; p["energy"] += 20
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == today - timedelta(days=1) else 1
        p["last_daily"] = today
        return await update.message.reply_text(f"🎁 +50 credits, +20 energy. Streak: {p['daily_streak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("Count must be a number.")
        if p["energy"] < count * 5:
            return await update.message.reply_text("Not enough energy.")
        if p["last_mine"] and now - p["last_mine"] < timedelta(minutes=2):
            return await update.message.reply_text("Cooldown active. Wait a bit.")
        ore_gain = 20 * count + (p["refinery_level"] * 5)
        p["ore"] += ore_gain; p["energy"] -= count * 5; p["credits"] += 10 * count
        p["last_mine"] = now
        return await update.message.reply_text(f"⛏️ Mined {ore_gain} ore. +{10*count} credits.")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types:
            return await update.message.reply_text("Usage: ,forge <unit> <count>")
        unit, amt = parts[1], int(parts[2])
        cost = {"scout": (10, 5), "drone": (15, 10), "tank": (30, 20)}[unit]
        if p["ore"] < cost[0]*amt or p["credits"] < cost[1]*amt:
            return await update.message.reply_text("Not enough ore/credits.")
        p["ore"] -= cost[0]*amt; p["credits"] -= cost[1]*amt; p["army"][unit] += amt
        return await update.message.reply_text(f"🛠️ Forged {amt} {unit}(s).")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",map"):
        out = "🌐 Zone Control:\n"
        for z, o in zones.items():
            name = players.get(o, {}).get("name", "Unclaimed")
            out += f"{z}: {name}\n"
        return await update.message.reply_text(out)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in zones:
            return await update.message.reply_text("Usage: ,claim <zone>")
        if p["credits"] < 100:
            return await update.message.reply_text("Need 100 credits.")
        zones[parts[1]] = cid; p["zone"] = parts[1]; p["credits"] -= 100
        return await update.message.reply_text(f"🚩 You now control {parts[1]}.")

    if text.startswith(",missions"):
        return await update.message.reply_text("🎯 Mission system coming soon.")

    if text.startswith(",blackmarket"):
        bm_text = "🛒 Black Market Items:\n"
        for item, price in bm_prices.items():
            bm_text += f"• {item} — {price} credits\n"
        return await update.message.reply_text(bm_text)

    if text.startswith(",unlockbm"):
        if p["blackmarket_unlocked"]:
            return await update.message.reply_text("✅ Black Market already unlocked.")
        if p["credits"] < bm_unlock_price:
            return await update.message.reply_text(f"❌ Need {bm_unlock_price} credits to unlock.")
        p["credits"] -= bm_unlock_price
        p["blackmarket_unlocked"] = True
        return await update.message.reply_text("🔓 Black Market access unlocked!")

    if text.startswith(",buybm"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buybm <item>")
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("🔒 Unlock Black Market first with ,unlockbm")
        item_id = parts[1]
        if item_id not in bm_prices:
            return await update.message.reply_text("❌ Item not found.")
        price = bm_prices[item_id]
        if p["credits"] < price:
            return await update.message.reply_text(f"❌ Not enough credits (need {price}).")
        give_item(p, item_id)
        p["credits"] -= price
        return await update.message.reply_text(f"✅ Purchased {item_id} for {price} credits.")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,daily ,mine ,forge ,use <item> ,map ,claim ,missions ,blackmarket ,unlockbm ,buybm")

    await update.message.reply_text("❓ Unknown command. Use ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
