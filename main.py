# SkyHustle - Phase 13: Combat Modifiers from Tech

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

def calculate_power(player):
    army = player["army"]
    base = army["scout"] * 5 + army["drone"] * 10 + army["tank"] * 20
    armor_bonus = player["research"].get("armor", 0) * 0.1
    return int(base * (1 + armor_bonus))

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
        power = calculate_power(p)
        return await update.message.reply_text(
            f"👤 {p['name']}
Ore: {p['ore']} | Energy: {p['energy']} | Credits: {p['credits']}
"
            f"Research: {p['research']}\n🛡 Power: {power}"
        )

    if text.startswith(",fight"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,fight <opponent_name>")
        opponent_name = parts[1].lower()
        opponent = None
        for other in players.values():
            if other["name"].lower() == opponent_name:
                opponent = other
                break
        if not opponent:
            return await update.message.reply_text("❌ Opponent not found.")
        my_power = calculate_power(p)
        opp_power = calculate_power(opponent)
        result = "won" if my_power >= opp_power else "lost"
        return await update.message.reply_text(
            f"⚔️ You {result}!
Your Power: {my_power} vs {opponent['name']}'s Power: {opp_power}")

    if text.startswith(",tech"):
        return await update.message.reply_text(
            f"🔬 Tech: {p['research']}\nCurrently Researching: {p.get('researching') or 'None'}")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,mine ,research ,tech ,build ,fight")

    await update.message.reply_text("❓ Unknown command. Use ,help.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
