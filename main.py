# SkyHustle - Phase 12: Research System + Tech Tree

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta, date
import os, json, random

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
items = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "drone", "tank"]
missions = {}
event_data = {"type": None, "reward": 0, "day": None}
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
        "army": {u: 0 for u in unit_types},
        "research": {"speed": 0, "armor": 0},
        "researching": None, "research_end": None,
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(), "items": {},
        "blackmarket_unlocked": False,
        "event_claimed": None
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

def get_build_cost(building, level):
    base = building_costs[building]["base_cost"]
    return int(base * (1.5 ** (level - 1)))

def new_world_event():
    today = date.today()
    if event_data["day"] == today:
        return
    event_data["day"] = today
    event_data["type"] = random.choice(["Ore Boost", "Energy Surge", "Credit Windfall"])
    event_data["reward"] = random.randint(50, 150)

# --------- Commands ---------
async def handle_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE, p):
    parts = update.message.text.strip().split()
    if len(parts) != 2:
        return await update.message.reply_text("⚙️ Usage: ,build <refinery|lab|defensetower|spycenter>")
    building = parts[1].lower()
    if building not in building_costs:
        return await update.message.reply_text("⚙️ Invalid building.")
    level = p.get(f"{building}_level", 0)
    cost = get_build_cost(building, level + 1)
    if p["credits"] < cost:
        return await update.message.reply_text(f"💳 Need {cost} credits to upgrade {building}.")
    p["credits"] -= cost
    p[f"{building}_level"] = level + 1
    return await update.message.reply_text(f"🏗️ {building.capitalize()} upgraded to Level {level+1}!")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()
    new_world_event()

    if text.startswith(",start"):
        return await update.message.reply_text("SkyHustle launched! Use ,name to begin.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("Usage: ,name <alias>")
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        research = p.get("research", {})
        researching = p.get("researching")
        remaining = ""
        if researching and p.get("research_end"):
            end = datetime.fromisoformat(p["research_end"])
            remaining = f"\n🔬 Researching {researching} (ends in {(end - now).seconds // 60}m)"
        return await update.message.reply_text(
            f"👤 {p['name']}\nOre: {p['ore']} | Energy: {p['energy']} | Credits: {p['credits']}\n"
            f"Research: {research}\n{remaining or ''}"
        )

    if text.startswith(",tech"):
        techs = p.get("research", {})
        lines = [f"🔬 {k}: Lv{v}" for k, v in techs.items()]
        return await update.message.reply_text("\n".join(lines) or "You have no research yet.")

    if text.startswith(",research"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,research <speed|armor>")
        if p.get("researching"):
            return await update.message.reply_text("⏳ You're already researching!")
        tech = parts[1].lower()
        if tech not in ["speed", "armor"]:
            return await update.message.reply_text("Invalid tech. Use: speed or armor")
        cost = 100 + p["research"].get(tech, 0) * 75
        duration = timedelta(minutes=5)
        if p["credits"] < cost:
            return await update.message.reply_text(f"Not enough credits ({cost} required).")
        p["credits"] -= cost
        p["researching"] = tech
        p["research_end"] = (now + duration).isoformat()
        return await update.message.reply_text(f"🔬 Researching {tech}! Will complete in {duration.seconds//60} minutes.")

    # Check for completed research
    if p.get("researching") and p.get("research_end"):
        end_time = datetime.fromisoformat(p["research_end"])
        if now >= end_time:
            tech = p["researching"]
            p["research"][tech] = p["research"].get(tech, 0) + 1
            p["researching"] = None
            p["research_end"] = None
            await update.message.reply_text(f"✅ {tech.capitalize()} research completed!")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3: return await update.message.reply_text("Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("Count must be number.")
        if p["energy"] < count * 5: return await update.message.reply_text("Not enough energy.")
        ore_gain = 20 * count + (p["refinery_level"] * 5) + p["research"].get("speed", 0) * 2
        p["ore"] += ore_gain
        p["energy"] -= count * 5
        return await update.message.reply_text(f"⛏️ Mined {ore_gain} ore.")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",event"):
        return await update.message.reply_text(
            f"🌍 Today's Event: {event_data['type']}\n🎁 Reward: {event_data['reward']} credits"
        )

    if text.startswith(",claimevent"):
        if p.get("event_claimed") == str(today):
            return await update.message.reply_text("✅ Already claimed today's event.")
        p["credits"] += event_data["reward"]
        p["event_claimed"] = str(today)
        return await update.message.reply_text(f"🎁 You claimed {event_data['reward']} credits.")

    if text.startswith(",build"):
        return await handle_build(update, ctx, p)

    if text.startswith(",help"):
        return await update.message.reply_text(
            "🛠️ Commands: ,start ,name ,status ,mine ,tech ,research ,event ,claimevent ,build ,use"
        )

    await update.message.reply_text("❓ Unknown command. Use ,help.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
