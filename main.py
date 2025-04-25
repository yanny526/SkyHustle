# SkyHustle - Phase 17–20 Update
# Massive update: Faction Wars, PvP Rankings, War Logs, and Seasonal Rewards

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
war_logs = []
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

def faction_bonus(p):
    if not p["faction"] or p["faction"] not in factions:
        return 1.0
    member_count = len(factions[p["faction"]]["members"])
    bonus = 1 + (member_count * 0.02)
    return bonus

def record_battle(attacker, defender, result):
    war_logs.append({
        "attacker": attacker["name"],
        "defender": defender["name"],
        "result": result,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def resolve_pvp(attacker, defender):
    atk_power = sum(attacker["army"].values())
    def_power = sum(defender["army"].values())
    if atk_power == def_power:
        result = "Draw"
    elif atk_power > def_power:
        attacker["wins"] += 1
        defender["losses"] += 1
        result = "Victory"
    else:
        attacker["losses"] += 1
        defender["wins"] += 1
        result = "Defeat"
    record_battle(attacker, defender, result)
    return result

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
        if not alias:
            return await update.message.reply_text("Usage: ,name <alias>")
        ocid, _ = find_by_name(alias)
        if ocid and ocid != cid:
            return await update.message.reply_text("Alias taken.")
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        items_owned = ", ".join([f"{k} x{v}" for k, v in p["items"].items()]) or "None"
        return await update.message.reply_text(
            f"Name: {p['name']}\nOre: {p['ore']}\nEnergy: {p['energy']}\nCredits: {p['credits']}\n"
            f"Army: {p['army']}\nItems: {items_owned}\nFaction: {p['faction'] or 'None'}\n"
            f"Wins: {p['wins']} | Losses: {p['losses']}\nShield: {shield}")

    if text.startswith(",daily"):
        if p["last_daily"] == today:
            return await update.message.reply_text("Already claimed today.")
        bonus = faction_bonus(p)
        p["credits"] += int(50 * bonus)
        p["energy"] += 20
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == today - timedelta(days=1) else 1
        p["last_daily"] = today
        return await update.message.reply_text(f"+{int(50*bonus)} credits, +20 energy. Streak: {p['daily_streak']} days.")

    if text.startswith(",fight"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,fight <opponent_name>")
        _, target = find_by_name(parts[1])
        if not target:
            return await update.message.reply_text("Opponent not found.")
        outcome = resolve_pvp(p, target)
        return await update.message.reply_text(f"⚔️ Result: {outcome}")

    if text.startswith(",rankings"):
        sorted_players = sorted(players.items(), key=lambda x: x[1]["wins"], reverse=True)
        out = "🏆 Top Commanders:\n"
        for i, (cid, user) in enumerate(sorted_players[:10]):
            out += f"{i+1}. {user['name']} - {user['wins']} wins\n"
        return await update.message.reply_text(out)

    if text.startswith(",warlog"):
        logs = war_logs[-10:]
        out = "📜 War Log (last 10):\n"
        for entry in logs:
            out += f"{entry['time']} - {entry['attacker']} vs {entry['defender']} - {entry['result']}\n"
        return await update.message.reply_text(out)

    if text.startswith(",rewards"):
        if p["wins"] >= 5:
            p["credits"] += 200
            return await update.message.reply_text("🎖 You claimed 200 credits for PvP excellence!")
        return await update.message.reply_text("❌ Win at least 5 PvP battles to claim seasonal rewards.")

    if text.startswith(",help"):
        return await update.message.reply_text("Commands: ,start ,name ,status ,daily ,fight ,rankings ,warlog ,rewards")

    await update.message.reply_text("Unknown command. Use ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
