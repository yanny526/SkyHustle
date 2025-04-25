# SkyHustle - Phase 10 Upgrade
# Core game + Items + Black Market + Building System

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os, json

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
items = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "drone", "tank"]
missions = {}
building_costs = {
    "refinery": {"base_cost": 100},
    "lab": {"base_cost": 150},
    "defensetower": {"base_cost": 120},
    "spycenter": {"base_cost": 130},
}
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "infinityscout2": {"type": "perishable", "desc": "Super scout (better detection)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
}

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(), "items": {},
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

def get_build_cost(building, level):
    base = building_costs[building]["base_cost"]
    return int(base * (1.5 ** (level - 1)))

async def handle_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE, p):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) != 2:
        return await update.message.reply_text("⚙️ Usage: ,build <refinery|lab|defensetower|spycenter>")

    building = parts[1].lower()

    if building not in building_costs:
        return await update.message.reply_text("⚙️ Invalid building.")

    level = 0
    if building == "refinery":
        level = p.get("refinery_level", 0)
    elif building == "lab":
        level = p.get("lab_level", 0)
    elif building == "defensetower":
        level = p.get("defense_level", 0)
    elif building == "spycenter":
        level = p.get("spy_level", 0)

    cost = get_build_cost(building, level + 1)

    if p["credits"] < cost:
        return await update.message.reply_text(f"💳 Need {cost} credits to upgrade {building} (current level: {level}).")

    # Deduct and upgrade
    p["credits"] -= cost
    if building == "refinery":
        p["refinery_level"] += 1
    elif building == "lab":
        p["lab_level"] += 1
    elif building == "defensetower":
        p["defense_level"] += 1
    elif building == "spycenter":
        p["spy_level"] += 1

    return await update.message.reply_text(f"🏗️ {building.capitalize()} upgraded to Level {level+1}! (Cost: {cost} credits)")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        return await update.message.reply_text("SkyHustle launched! Use ,name to begin.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("Usage: ,name <alias>")
        ocid, _ = find_by_name(alias)
        if ocid and ocid != cid: return await update.message.reply_text("Alias taken.")
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        items_owned = ", ".join([f"{k} x{v}" for k,v in p["items"].items()]) or "None"
        return await update.message.reply_text(
            f"Name: {p['name']}\nOre: {p['ore']}\nEnergy: {p['energy']}\nCredits: {p['credits']}\n"
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']} | Defense Lv{p['defense_level']}\n"
            f"Spy Lv{p['spy_level']}\nArmy: {p['army']}\nItems: {items_owned}\nShield: {shield}"
        )

    if text.startswith(",daily"):
        if p["last_daily"] == today:
            return await update.message.reply_text("Already claimed today.")
        p["credits"] += 50
        p["energy"] += 20
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == today - timedelta(days=1) else 1
        p["last_daily"] = today
        return await update.message.reply_text(f"+50 credits, +20 energy. Streak: {p['daily_streak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("Count must be a number.")
        if p["energy"] < count * 5:
            return await update.message.reply_text("Not enough energy.")
        if p["last_mine"] and now - p["last_mine"] < timedelta(minutes=2):
            return await update.message.reply_text("Cooldown active. Wait a bit.")
        ore_gain = 20 * count + (p["refinery_level"] * 5)
        p["ore"] += ore_gain
        p["energy"] -= count * 5
        p["credits"] += 10 * count
        p["last_mine"] = now
        return await update.message.reply_text(f"Mined {ore_gain} ore. +{10*count} credits.")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types:
            return await update.message.reply_text("Usage: ,forge <unit> <count>")
        unit, amt = parts[1], int(parts[2])
        cost = {"scout": (10, 5), "drone": (15, 10), "tank": (30, 20)}[unit]
        if p["ore"] < cost[0]*amt or p["credits"] < cost[1]*amt:
            return await update.message.reply_text("Not enough ore/credits.")
        p["ore"] -= cost[0]*amt
        p["credits"] -= cost[1]*amt
        p["army"][unit] += amt
        return await update.message.reply_text(f"Forged {amt} {unit}(s).")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",map"):
        out = "Zone Control:\n"
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
        zones[parts[1]] = cid
        p["zone"] = parts[1]
        p["credits"] -= 100
        return await update.message.reply_text(f"You now control {parts[1]}.")

    if text.startswith(",build"):
        return await handle_build(update, ctx, p)

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,daily ,mine ,forge ,use <item> ,map ,claim ,build"
        )

    await update.message.reply_text("Unknown command. Use ,help.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
