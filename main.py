# SkyHustle - Hyperdrive Code (Phase 1–56)
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import os, json

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "drone", "tank", "elite"]
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "infinityscout2": {"type": "perishable", "desc": "Advanced scout (2x stronger)"},
    "reviveall": {"type": "perishable", "desc": "Revive all non-premium units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
    "empdevice": {"type": "perishable", "desc": "Disable enemy defenses for 1 raid"},
    "advancedshield": {"type": "passive", "desc": "Auto-block first daily attack"},
}
missions = {}
world_boss = {"hp": 5000, "max_hp": 5000, "rewards": 500}
seasons = {"season_active": False, "top_players": []}

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "refinery_level": 0, "lab_level": 0, "spy_level": 0, "defense_level": 0,
        "army": {u: 0 for u in unit_types}, "items": {},
        "daily_streak": 0, "last_daily": None, "wins": 0, "losses": 0,
        "rank": 0, "faction": None, "blackmarket_unlocked": False,
        "pvp_score": 1000
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
        return False, "Invalid item."
    if p["items"].get(item_id, 0) <= 0:
        return False, "You don't own this item."
    if item_defs[item_id]["type"] == "perishable":
        p["items"][item_id] -= 1
        if p["items"][item_id] == 0:
            del p["items"][item_id]
    return True, f"Used {item_id}"

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = datetime.today().date()

    if text.startswith(",start"):
        return await update.message.reply_text("SkyHustle ready. Use ,name <alias>.")

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
            f"Name: {p['name']}\nOre: {p['ore']} Energy: {p['energy']} Credits: {p['credits']}\n"
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\nArmy: {p['army']}\n"
            f"Items: {items_owned}\nShield: {shield}")

    if text.startswith(",daily"):
        if p["last_daily"] == str(today):
            return await update.message.reply_text("Already claimed today.")
        p["credits"] += 50
        p["energy"] += 20
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == str(today - timedelta(days=1)) else 1
        p["last_daily"] = str(today)
        return await update.message.reply_text(f"+50 credits, +20 energy. Streak {p['daily_streak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("Count must be number.")
        if p["energy"] < count * 5:
            return await update.message.reply_text("Not enough energy.")
        ore_gain = 20 * count
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
        cost = {"scout": (10, 5), "drone": (15, 10), "tank": (30, 20), "elite": (100, 80)}[unit]
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
        out = "Zones:\n"
        for z, o in zones.items():
            owner = players.get(o, {}).get("name", "Unclaimed")
            out += f"{z}: {owner}\n"
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
        return await update.message.reply_text(f"Zone {parts[1]} claimed.")

    if text.startswith(",raid"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,raid <enemy_name>")
        enemy_name = parts[1]
        eid, ep = find_by_name(enemy_name)
        if not ep:
            return await update.message.reply_text("Enemy not found.")
        if ep["shield"] and now < ep["shield"]:
            return await update.message.reply_text("Target shielded.")
        steal = min(ep["credits"]//5, 100)
        p["credits"] += steal
        ep["credits"] -= steal
        p["wins"] += 1
        ep["losses"] += 1
        return await update.message.reply_text(f"Raided {enemy_name}! Stole {steal} credits!")

    if text.startswith(",bossattack"):
        dmg = 50
        world_boss["hp"] -= dmg
        reward = 10
        p["credits"] += reward
        return await update.message.reply_text(f"Dealt {dmg} damage to Boss! +{reward} credits.")

    if text.startswith(",blackmarket"):
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("Black Market locked. Buy access.")
        return await update.message.reply_text("Black Market items: infinityscout1, reviveall, hazmat, empdevice, advancedshield.")

    if text.startswith(",buyblackmarket"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buyblackmarket <item>")
        item = parts[1]
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("Unlock Black Market first.")
        price = {"infinityscout1": 200, "reviveall": 500, "hazmat": 250, "empdevice": 300, "advancedshield": 400}
        if p["credits"] < price.get(item, 9999):
            return await update.message.reply_text("Not enough credits.")
        p["credits"] -= price[item]
        give_item(p, item)
        return await update.message.reply_text(f"Purchased {item}!")

    if text.startswith(",unlockblackmarket"):
        if p["credits"] < 500:
            return await update.message.reply_text("500 credits needed to unlock.")
        p["credits"] -= 500
        p["blackmarket_unlocked"] = True
        return await update.message.reply_text("Black Market unlocked!")

    if text.startswith(",help"):
        return await update.message.reply_text("Commands: ,start ,name ,status ,daily ,mine ,forge ,use ,map ,claim ,raid ,bossattack ,blackmarket ,buyblackmarket ,unlockblackmarket")

    await update.message.reply_text("Unknown command. Use ,help.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
