# SkyHustle Full Phase 24 Update (Zone Buffs + Supply Drops + Boss Raids)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os, json, random

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
zone_bonuses = {"Alpha": "Mine +10%", "Beta": "Defense +5%", "Gamma": "Energy Regen +10%", "Delta": "Ore Storage +10%", "Epsilon": "Tech Speed +10%"}
boss_health = 1000
unit_types = ["scout", "drone", "tank"]

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(), "items": {}
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global boss_health
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        return await update.message.reply_text("SkyHustle Phase 24 ready! Use ,name to begin.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("Usage: ,name <alias>")
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        return await update.message.reply_text(
            f"Name: {p['name']}\nOre: {p['ore']}\nEnergy: {p['energy']}\nCredits: {p['credits']}\n"
            f"Zone: {p['zone'] or 'None'}\nShield: {shield}\nArmy: {p['army']}"
        )

    if text.startswith(",map"):
        out = "🌍 Zone Control Map:\n"
        for z, o in zones.items():
            name = players.get(o, {}).get("name", "Unclaimed")
            bonus = zone_bonuses[z]
            out += f"{z}: {name} [{bonus}]\n"
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
        return await update.message.reply_text(f"🚩 You now control {parts[1]}!")

    if text.startswith(",supplydrop"):
        if p["zone"] is None:
            return await update.message.reply_text("You must control a zone to get supply drops!")
        reward = random.randint(50,150)
        p["credits"] += reward
        return await update.message.reply_text(f"🎁 Supply Drop collected! +{reward} credits!")

    if text.startswith(",boss"):
        dmg = random.randint(50,150)
        boss_health -= dmg
        if boss_health <= 0:
            boss_health = 1000
            reward = 500
            p["credits"] += reward
            return await update.message.reply_text(f"🔥 Boss defeated! You earned {reward} credits!")
        return await update.message.reply_text(f"⚔️ You dealt {dmg} damage to the boss! Boss health: {boss_health}")

    if text.startswith(",daily"):
        if p["last_daily"] == today:
            return await update.message.reply_text("Already claimed today.")
        p["credits"] += 50
        p["energy"] += 20
        p["daily_streak"] = p["daily_streak"] + 1 if p["last_daily"] == today - timedelta(days=1) else 1
        p["last_daily"] = today
        return await update.message.reply_text(f"+50 credits, +20 energy. Streak: {p['daily_streak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("Count must be a number.")
        if p["energy"] < count * 5:
            return await update.message.reply_text("Not enough energy.")
        ore_gain = 20 * count
        p["ore"] += ore_gain
        p["energy"] -= count * 5
        p["credits"] += 10 * count
        return await update.message.reply_text(f"Mined {ore_gain} ore. +{10*count} credits.")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,map ,claim ,supplydrop ,boss ,daily ,mine"
        )

    await update.message.reply_text("❓ Unknown command. Type ,help.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
