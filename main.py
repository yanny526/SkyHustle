# SkyHustle - Phase 6 (Polished)
# Adds Factions, PvP Rank, and Faction Stats

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os, json

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "drone", "tank"]
factions = {}

# ------------------- PLAYER SYSTEM -------------------
def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "refinery_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types},
        "wins": 0, "losses": 0, "rank": 0,
        "last_daily": None, "daily_streak": 0,
        "faction": None, "items": {}
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

# ------------------- FACTIONS -------------------
def create_faction(name):
    if name in factions:
        return False
    factions[name] = {"members": [], "bank": 0, "wins": 0, "banner": ""}
    return True

def join_faction(player, name):
    if name not in factions:
        return False, "Faction does not exist."
    if player["faction"]:
        return False, "You are already in a faction."
    player["faction"] = name
    factions[name]["members"].append(player["name"])
    return True, f"Joined faction {name}."

def leave_faction(player):
    f = player["faction"]
    if f and player["name"] in factions[f]["members"]:
        factions[f]["members"].remove(player["name"])
    player["faction"] = None

# ------------------- COMMANDS -------------------
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        return await update.message.reply_text("Welcome to SkyHustle! Use ,name <alias> to get started.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("Usage: ,name <alias>")
        ocid, _ = find_by_name(alias)
        if ocid and ocid != cid:
            return await update.message.reply_text("❌ Alias taken.")
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        return await update.message.reply_text(
            f"📊 Name: {p['name'] or 'Commander'}\nFaction: {p['faction'] or 'None'}\n"
            f"Ore: {p['ore']}  Energy: {p['energy']}  Credits: {p['credits']}\n"
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\n"
            f"Rank: {p['rank']} (W: {p['wins']} / L: {p['losses']})\n"
            f"Army: {p['army']}"
        )

    if text.startswith(",daily"):
        if p["last_daily"] == today:
            return await update.message.reply_text("🎁 Already claimed today.")
        p["credits"] += 50
        p["energy"] += 25
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == today - timedelta(days=1) else 1
        p["last_daily"] = today
        return await update.message.reply_text(f"🎁 +50 credits, +25 energy. Streak: {p['daily_streak']} days.")

    if text.startswith(",faction"):
        parts = text.split()
        if len(parts) < 2:
            return await update.message.reply_text("Usage: ,faction create/join/leave <name>")
        cmd = parts[1]
        if cmd == "create" and len(parts) == 3:
            if create_faction(parts[2]):
                p["faction"] = parts[2]
                factions[parts[2]]["members"].append(p["name"])
                return await update.message.reply_text(f"✅ Faction {parts[2]} created.")
            return await update.message.reply_text("❌ Faction name already exists.")
        elif cmd == "join" and len(parts) == 3:
            success, msg = join_faction(p, parts[2])
            return await update.message.reply_text(("✅ " if success else "❌ ") + msg)
        elif cmd == "leave":
            leave_faction(p)
            return await update.message.reply_text("👋 You left your faction.")
        return await update.message.reply_text("❌ Invalid faction command.")

    if text.startswith(",rank"):
        top = sorted(players.values(), key=lambda x: x["rank"], reverse=True)[:5]
        board = "🏆 Top Commanders:\n" + "\n".join([
            f"{i+1}. {pl['name']} - {pl['rank']} RP" for i, pl in enumerate(top)
        ])
        return await update.message.reply_text(board)

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,daily ,faction create/join/leave <name> ,rank")

    await update.message.reply_text("❓ Unknown command. Use ,help")

# ------------------- START BOT -------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
