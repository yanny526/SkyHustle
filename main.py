# SkyHustle - Phase 6: Factions, PvP Ranking, and Map Control

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
factions = {}
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
}

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 1000, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(), "items": {}
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
            f"Rank: {p['rank']} | Faction: {p['faction'] or 'None'}\n"
            f"Army: {p['army']}\nItems: {items_owned}\nShield: {shield}")

    if text.startswith(",faction"):
        parts = text.split()
        if len(parts) < 2:
            return await update.message.reply_text("Usage: ,faction create/join/leave <name>")
        cmd = parts[1].lower()
        if cmd == "create" and len(parts) == 3:
            name = parts[2]
            if name in factions:
                return await update.message.reply_text("❌ Faction already exists.")
            factions[name] = {"members": set([cid])}
            p["faction"] = name
            return await update.message.reply_text(f"🏳️ Created and joined faction {name}.")
        elif cmd == "join" and len(parts) == 3:
            name = parts[2]
            if name not in factions:
                return await update.message.reply_text("❌ No such faction.")
            factions[name]["members"].add(cid)
            p["faction"] = name
            return await update.message.reply_text(f"🤝 Joined faction {name}.")
        elif cmd == "leave":
            f = p["faction"]
            if f and cid in factions[f]["members"]:
                factions[f]["members"].remove(cid)
            p["faction"] = None
            return await update.message.reply_text("🚪 You left your faction.")

    if text.startswith(",rank"):
        top = sorted(players.items(), key=lambda x: x[1]["rank"], reverse=True)[:5]
        out = "🏆 Top 5 Commanders:\n"
        for i, (_, pl) in enumerate(top, 1):
            out += f"{i}. {pl['name'] or 'Unnamed'} – {pl['rank']} RP\n"
        return await update.message.reply_text(out)

    return await update.message.reply_text("Unknown command. Use ,status ,faction or ,rank")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
