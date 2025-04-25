# SkyHustle - Phase 7
# Includes missions, black market, premium store, zone control, cosmetics (banners and skins)

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
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
}

skins_available = {
    "default": {"name": "Standard Army", "unlock": "free"},
    "metallic": {"name": "Metallic Armor", "unlock": "Rank 10+"},
    "stealth": {"name": "Stealth Units", "unlock": "Black Market Only"},
    "golden": {"name": "Golden Troops", "unlock": "Rank 50+"},
}

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types},
        "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0,
        "daily_streak": 0, "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(),
        "items": {},
        "banner": None,
        "skin": None,
        "unlocked_skins": []
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
        current_skin = p["skin"] or "default"
        return await update.message.reply_text(
            f"Name: {p['name']}\nOre: {p['ore']} | Energy: {p['energy']} | Credits: {p['credits']}\n"
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\n"
            f"Army: {p['army']}\nItems: {items_owned}\n"
            f"Banner: {p['banner'] or 'None'} | Skin: {skins_available[current_skin]['name']}\n"
            f"Shield: {shield}")

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
            return await update.message.reply_text("⚡ Not enough energy.")
        if p["last_mine"] and now - p["last_mine"] < timedelta(minutes=2):
            return await update.message.reply_text("⌛ Cooldown active.")
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
            return await update.message.reply_text("⚠️ Not enough ore/credits.")
        p["ore"] -= cost[0]*amt; p["credits"] -= cost[1]*amt; p["army"][unit] += amt
        return await update.message.reply_text(f"🔧 Forged {amt} {unit}(s).")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",map"):
        out = "🗺 Zone Control:\n"
        for z, o in zones.items():
            name = players.get(o, {}).get("name", "Unclaimed")
            out += f"{z}: {name}\n"
        return await update.message.reply_text(out)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in zones:
            return await update.message.reply_text("Usage: ,claim <zone>")
        if p["credits"] < 100:
            return await update.message.reply_text("⚠️ Need 100 credits.")
        zones[parts[1]] = cid; p["zone"] = parts[1]; p["credits"] -= 100
        return await update.message.reply_text(f"🏴‍☠️ You now control {parts[1]}.")

    if text.startswith(",missions"):
        return await update.message.reply_text("🎯 Mission system coming soon.")

    # 🏳 Banners
    if text.startswith(",setbanner"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,setbanner <emoji>")
        banner = parts[1]
        p["banner"] = banner
        return await update.message.reply_text(f"🏳️ Banner set to {banner}.")

    if text.startswith(",mybanner"):
        if not p["banner"]:
            return await update.message.reply_text("No banner set.")
        return await update.message.reply_text(f"🏴 Current banner: {p['banner']}")

    # 🎨 Skins
    if text.startswith(",skins"):
        out = "🎨 Available Skins:\n"
        for sk, info in skins_available.items():
            out += f"{sk}: {info['name']} ({info['unlock']})\n"
        return await update.message.reply_text(out)

    if text.startswith(",setskin"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,setskin <skinname>")
        skin = parts[1]
        if skin not in skins_available:
            return await update.message.reply_text("Invalid skin name.")
        if skin not in p["unlocked_skins"] and skin != "default":
            return await update.message.reply_text("🔒 You have not unlocked this skin.")
        p["skin"] = skin
        return await update.message.reply_text(f"🎨 Equipped skin: {skins_available[skin]['name']}.")

    if text.startswith(",myskin"):
        current = p["skin"] or "default"
        return await update.message.reply_text(f"🎨 Current skin: {skins_available[current]['name']}")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands:\n"
            ",start ,name ,status ,daily ,mine ,forge ,use <item> ,map ,claim ,missions\n"
            "Cosmetics: ,setbanner <emoji> ,mybanner ,skins ,setskin <skinname> ,myskin"
        )

    await update.message.reply_text("❓ Unknown command. Type ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
