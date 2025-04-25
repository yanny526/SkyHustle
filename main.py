# SkyHustle - Phase 4 Upgrade
# Adds Missions, Player Rank, PvP Stats, and Leaderboards

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

mission_defs = {
    "daily_mine": {"desc": "Mine ore 3 times", "goal": 3, "reward": {"credits": 25}},
    "daily_fight": {"desc": "Win 1 battle", "goal": 1, "reward": {"rank": 5}},
    "lab_upgrade": {"desc": "Reach Lab Level 2", "goal": 2, "reward": {"credits": 50}},
}


def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(), "items": {}, "missions": {}
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

    def update_mission(key):
        p["missions"].setdefault(key, 0)
        p["missions"][key] += 1

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
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\nArmy: {p['army']}\n"
            f"Wins: {p['wins']}  Losses: {p['losses']}  Rank: {p['rank']}\n"
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
        update_mission("daily_mine")
        return await update.message.reply_text(f"Mined {ore_gain} ore. +{10*count} credits.")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types:
            return await update.message.reply_text("Usage: ,forge <unit> <count>")
        unit, amt = parts[1], int(parts[2])
        cost = {"scout": (10, 5), "drone": (15, 10), "tank": (30, 20)}[unit]
        if p["ore"] < cost[0]*amt or p["credits"] < cost[1]*amt:
            return await update.message.reply_text("Not enough ore/credits.")
        p["ore"] -= cost[0]*amt; p["credits"] -= cost[1]*amt; p["army"][unit] += amt
        return await update.message.reply_text(f"Forged {amt} {unit}(s).")

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2: return await update.message.reply_text("Usage: ,attack <player>")
        tcid, tp = find_by_name(parts[1])
        if not tp: return await update.message.reply_text("Player not found.")
        power = sum(p["army"].values()) * 10 + p["rank"]
        defense = sum(tp["army"].values()) * 10 + tp["rank"]
        win = power >= defense
        if win:
            p["wins"] += 1; tp["losses"] += 1; p["rank"] += 10
            update_mission("daily_fight")
        else:
            p["losses"] += 1; tp["wins"] += 1; p["rank"] = max(0, p["rank"] - 5)
        return await update.message.reply_text("Victory!" if win else "Defeat.")

    if text.startswith(",scout"):
        parts = text.split()
        if len(parts) != 2: return await update.message.reply_text("Usage: ,scout <player>")
        tcid, tp = find_by_name(parts[1])
        if not tp: return await update.message.reply_text("Player not found.")
        return await update.message.reply_text(f"{parts[1]} → Army: {tp['army']} | Def L{tp['defense_level']}")

    if text.startswith(",build"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in ["refinery", "lab", "defense", "spy"]:
            return await update.message.reply_text("Usage: ,build <refinery|lab|defense|spy>")
        lvl = p[f"{parts[1]}_level"]
        cost = (lvl + 1) * 100
        if p["credits"] < cost:
            return await update.message.reply_text(f"Need {cost} credits.")
        p["credits"] -= cost
        p[f"{parts[1]}_level"] += 1
        return await update.message.reply_text(f"{parts[1].capitalize()} upgraded to L{p[f'{parts[1]}_level']}")

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
        zones[parts[1]] = cid; p["zone"] = parts[1]; p["credits"] -= 100
        return await update.message.reply_text(f"You now control {parts[1]}.")

    if text.startswith(",rank"):
        return await update.message.reply_text(f"Your Rank: {p['rank']} RP")

    if text.startswith(",top"):
        top = sorted(players.values(), key=lambda x: x["rank"], reverse=True)[:5]
        out = "🏆 Top Players:\n" + "\n".join([f"{i+1}. {p['name']} – {p['rank']} RP" for i, p in enumerate(top)])
        return await update.message.reply_text(out)

    if text.startswith(",missions"):
        out = "🎯 Missions:\n"
        for key, data in mission_defs.items():
            done = p["missions"].get(key, 0)
            out += f"- {data['desc']} ({done}/{data['goal']})\n"
        return await update.message.reply_text(out)

    if text.startswith(",claim mission"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("Usage: ,claim mission <mission_id>")
        mid = parts[2]
        if mid not in mission_defs:
            return await update.message.reply_text("No such mission.")
        if p["missions"].get(mid, 0) < mission_defs[mid]["goal"]:
            return await update.message.reply_text("Mission not complete yet.")
        reward = mission_defs[mid]["reward"]
        for k, v in reward.items():
            if k == "credits": p["credits"] += v
            elif k == "rank": p["rank"] += v
        p["missions"][mid] = 0
        return await update.message.reply_text("✅ Mission claimed!")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,daily ,mine ,forge ,build ,use ,map ,claim ,scout ,attack ,rank ,top ,missions ,claim mission <id>")

    await update.message.reply_text("Unknown command. Use ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
