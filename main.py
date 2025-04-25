# SkyHustle - Ultimate Expansion (Phase 28–30)
# Missions System, PvP Rank Overhaul, World Buffs & Penalties

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta, date
import os, json, random

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

# ====== DATA STRUCTURES ======
players = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "tank", "drone"]
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
}
factions = {}
market_offers = {}
offer_id = 1
events = {"meteor_shower": False, "storm": False}
missions = {}

# ====== HELPERS ======
def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "army": {u: 0 for u in unit_types},
        "research": {"speed": 0, "armor": 0},
        "items": {},
        "faction": None,
        "daily_streak": 0, "last_daily": None,
        "rank_points": 0,
        "active_missions": [],
        "completed_missions": []
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

def use_item(player, item):
    if item not in item_defs:
        return False, "❌ Invalid item."
    if player["items"].get(item, 0) <= 0:
        return False, "❌ You don't have this item."
    if item_defs[item]["type"] == "perishable":
        player["items"][item] -= 1
        if player["items"][item] == 0:
            del player["items"][item]
    return True, f"✅ Used {item}!"

def start_event():
    ev = random.choice(["meteor_shower", "storm"])
    events[ev] = True

def clear_events():
    for k in events:
        events[k] = False

def make_offer(seller, item, price):
    global offer_id
    market_offers[offer_id] = {"seller": seller, "item": item, "price": price}
    offer_id += 1

def generate_mission():
    mtype = random.choice(["mine", "forge", "scout"])
    if mtype == "mine":
        return {"type": "mine", "target": random.randint(100, 300)}
    if mtype == "forge":
        return {"type": "forge", "unit": random.choice(unit_types), "count": random.randint(1, 5)}
    if mtype == "scout":
        return {"type": "scout", "times": random.randint(1, 3)}

# ====== COMMANDS ======
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    player = get_player(cid)
    now = datetime.now()
    today = date.today()

    # Base Commands
    if text.startswith(",start"):
        return await update.message.reply_text("🚀 SkyHustle Ultimate Launched! Use ,name to set your callsign.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("⚠ Usage: ,name <alias>")
        player["name"] = alias
        return await update.message.reply_text(f"✅ Callsign set to {alias}.")

    if text.startswith(",status"):
        items_owned = ", ".join([f"{k}x{v}" for k,v in player["items"].items()]) or "None"
        return await update.message.reply_text(
            f"🧑‍🚀 {player['name']} Status\n"
            f"Ore: {player['ore']} | Energy: {player['energy']} | Credits: {player['credits']}\n"
            f"Army: {player['army']}\nItems: {items_owned}\nFaction: {player['faction'] or 'None'}\n"
            f"Rank Points: {player['rank_points']}")

    if text.startswith(",daily"):
        if player["last_daily"] == today:
            return await update.message.reply_text("⏳ Already claimed today.")
        player["credits"] += 50
        player["energy"] += 30
        player["last_daily"] = today
        player["daily_streak"] += 1
        return await update.message.reply_text(f"🎁 +50 credits, +30 energy! Streak: {player['daily_streak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚒️ Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("⚠ Count must be a number.")
        if player["energy"] < count * 5:
            return await update.message.reply_text("⚠ Not enough energy.")
        if player["last_mine"] and now - player["last_mine"] < timedelta(minutes=2):
            return await update.message.reply_text("⏳ Cooldown active.")
        gain = 20 * count
        player["ore"] += gain
        player["credits"] += 10 * count
        player["energy"] -= 5 * count
        player["last_mine"] = now
        return await update.message.reply_text(f"⛏️ Mined {gain} ore!")

    # Item Use
    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛠️ Usage: ,use <item>")
        success, msg = use_item(player, parts[1])
        return await update.message.reply_text(msg)

    # Join Faction
    if text.startswith(",join"):
        faction = text[6:].strip()
        if not faction:
            return await update.message.reply_text("⚔️ Usage: ,join <faction>")
        player["faction"] = faction
        factions.setdefault(faction, []).append(cid)
        return await update.message.reply_text(f"🏳️ Joined faction: {faction}")

    # Marketplace
    if text.startswith(",market"):
        if not market_offers:
            return await update.message.reply_text("🏪 No offers listed.")
        msg = "🏪 Market Offers:\n"
        for oid, offer in market_offers.items():
            seller = players.get(offer["seller"], {}).get("name", "Unknown")
            msg += f"ID:{oid} | {offer['item']} | {offer['price']} credits | Seller: {seller}\n"
        return await update.message.reply_text(msg)

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("💳 Usage: ,buy <offer_id>")
        oid = int(parts[1])
        offer = market_offers.get(oid)
        if not offer:
            return await update.message.reply_text("❌ Invalid offer ID.")
        if player["credits"] < offer["price"]:
            return await update.message.reply_text("❌ Not enough credits.")
        player["credits"] -= offer["price"]
        use_item(player, offer["item"])  # Immediately adds item
        del market_offers[oid]
        return await update.message.reply_text("✅ Purchase successful!")

    # Missions
    if text.startswith(",missions"):
        if not player["active_missions"]:
            mission = generate_mission()
            player["active_missions"].append(mission)
            return await update.message.reply_text(f"🎯 New Mission: {mission}")
        return await update.message.reply_text(f"🎯 Current Mission: {player['active_missions'][0]}")

    # World Event
    if text.startswith(",eventstatus"):
        active = [k for k,v in events.items() if v]
        if not active:
            return await update.message.reply_text("🌌 No active events.")
        return await update.message.reply_text(f"🔥 Active Events: {', '.join(active)}")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "🚀 Commands:\n,start ,name ,status ,daily ,mine ore <x>\n"
            ",use <item>\n"
            ",join <faction>\n"
            ",market\n"
            ",buy <id>\n"
            ",missions\n"
            ",eventstatus"
        )

    await update.message.reply_text("❓ Unknown command. Use ,help.")

# ====== MAIN RUNNER ======
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
