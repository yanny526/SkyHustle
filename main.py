# SkyHustle - Full Functional Codebase (Phase 3: Combat + Building + Store)

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
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
    "emp": {"type": "perishable", "desc": "Disables opponent’s defense for 1 attack"},
    "shieldplus": {"type": "passive", "desc": "Auto-blocks first attack daily"}
}


def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False, "items": {}, "blackmarket_level": 0
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

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
        return await update.message.reply_text("SkyHustle launched! Use ,name to begin.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        items_owned = ", ".join([f"{k} x{v}" for k,v in p["items"].items()]) or "None"
        return await update.message.reply_text(
            f"Name: {p['name']}\nOre: {p['ore']}\nEnergy: {p['energy']}\nCredits: {p['credits']}\n"
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\nArmy: {p['army']}\n"
            f"Items: {items_owned}\nShield: {shield}")

    if text.startswith(",daily"):
        if p["last_daily"] == today:
            return await update.message.reply_text("Already claimed today.")
        p["credits"] += 50; p["energy"] += 20
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == today - timedelta(days=1) else 1
        p["last_daily"] = today
        return await update.message.reply_text(f"+50 credits, +20 energy. Streak: {p['daily_streak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore": return await update.message.reply_text("Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("Count must be a number.")
        if p["energy"] < count * 5: return await update.message.reply_text("Not enough energy.")
        if p["last_mine"] and now - p["last_mine"] < timedelta(minutes=2):
            return await update.message.reply_text("Cooldown active.")
        gain = 20 * count + (p["refinery_level"] * 5)
        p["ore"] += gain; p["energy"] -= count * 5; p["credits"] += 10 * count; p["last_mine"] = now
        return await update.message.reply_text(f"⛏ Mined {gain} ore. +{10*count} credits")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types: return await update.message.reply_text("Usage: ,forge <unit> <count>")
        unit, amt = parts[1], int(parts[2])
        cost = {"scout": (10, 5), "drone": (15, 10), "tank": (30, 20)}[unit]
        if p["ore"] < cost[0]*amt or p["credits"] < cost[1]*amt:
            return await update.message.reply_text("Not enough resources.")
        p["ore"] -= cost[0]*amt; p["credits"] -= cost[1]*amt; p["army"][unit] += amt
        return await update.message.reply_text(f"🔧 Forged {amt} {unit}(s)")

    if text.startswith(",build"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in ["refinery", "defense", "lab", "spy"]:
            return await update.message.reply_text("Usage: ,build <refinery|defense|lab|spy>")
        field = parts[1] + "_level"
        lvl = p[field]; cost = (lvl+1) * 50
        if p["credits"] < cost: return await update.message.reply_text(f"Need {cost} credits.")
        p["credits"] -= cost; p[field] += 1
        return await update.message.reply_text(f"🏗 {parts[1].capitalize()} upgraded to L{p[field]}")

    if text.startswith(",scout"):
        parts = text.split()
        if len(parts) != 2: return await update.message.reply_text("Usage: ,scout <player>")
        tgt = parts[1]
        for cid2, t in players.items():
            if t["name"].lower() == tgt.lower():
                report = f"🕵 Recon Report on {t['name']}\nArmy: {t['army']}\nDefense Lv: {t['defense_level']}"
                return await update.message.reply_text(report)
        return await update.message.reply_text("Player not found.")

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2: return await update.message.reply_text("Usage: ,attack <player>")
        tgt = parts[1]
        for cid2, t in players.items():
            if t["name"].lower() == tgt.lower():
                atk_power = sum(p["army"].values()) * 10 + p["rank"]
                def_power = sum(t["army"].values()) * 10 + t["defense_level"] + t["rank"]
                win = atk_power >= def_power
                p["wins" if win else "losses"] += 1
                t["losses" if win else "wins"] += 1
                return await update.message.reply_text(f"⚔ {'Victory' if win else 'Defeat'} vs {t['name']}!")
        return await update.message.reply_text("Target not found.")

    if text.startswith(",store"):
        return await update.message.reply_text("🛒 Store: Coming soon. Resource packs, boost items, bundles.")

    if text.startswith(",blackmarket"):
        return await update.message.reply_text("🧪 Black Market unlocked with real currency. Type ,bm buy <item> lvX")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",map"):
        msg = "🌍 Zone Control:\n"
        for z, o in zones.items():
            msg += f"{z}: {players[o]['name'] if o else 'Unclaimed'}\n"
        return await update.message.reply_text(msg)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2: return await update.message.reply_text("Usage: ,claim <zone>")
        if p["credits"] < 100: return await update.message.reply_text("Need 100 credits.")
        z = parts[1]
        if z not in zones: return await update.message.reply_text("Invalid zone.")
        zones[z] = cid; p["zone"] = z; p["credits"] -= 100
        return await update.message.reply_text(f"✅ You now control {z}")

    if text.startswith(",help"):
        return await update.message.reply_text("Commands: ,start ,name ,status ,daily ,mine ,forge ,build ,scout ,attack ,use ,map ,claim ,store ,blackmarket")

    await update.message.reply_text("Unknown command. Use ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
