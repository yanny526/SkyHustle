# SkyHustle - Full Build (Phase 1–32)
# By Commander Yanny + Co-Commander Sky
# Full Game Logic: Mining, Forging, Zone Capture, Black Market, Premium Systems

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import os, json

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players = {}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "tank", "drone"]
blackmarket_items = {
    "infinityscout1": {"price": 100, "rarity": "Rare"},
    "infinityscout2": {"price": 250, "rarity": "Legendary"},
    "hazmat": {"price": 150, "rarity": "Rare"},
    "reviveall": {"price": 500, "rarity": "Legendary"}
}
store_packages = {
    "minerpack": {"price": 200, "desc": "Boost mining by 50% for 24h."},
    "warriorpack": {"price": 300, "desc": "Get 5 tanks and bonus armor."},
    "starterpack": {"price": 100, "desc": "Ore+Credits starter bundle."}
}

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100,
        "army": {u: 0 for u in unit_types},
        "items": {},
        "blackmarket_unlocked": False,
        "premium_spent": 0,
        "premium_level": 0
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()

    if text.startswith(",start"):
        return await update.message.reply_text("🌌 SkyHustle launched! Use ,name <alias> to begin your legend.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        p["name"] = alias
        return await update.message.reply_text(f"🚀 Callsign set to {alias}")

    if text.startswith(",status"):
        bm = "Unlocked" if p["blackmarket_unlocked"] else "Locked"
        items_owned = ", ".join([f"{k}x{v}" for k,v in p["items"].items()]) or "None"
        return await update.message.reply_text(
            f"👤 {p['name']}\n🪨 Ore: {p['ore']} ⚡ Energy: {p['energy']} 💳 Credits: {p['credits']}\n"
            f"🛡️ Shield: {p['shield'] or 'None'}\n🏰 Zone: {p['zone'] or 'None'}\n"
            f"🛒 BlackMarket: {bm}\n🎖️ Premium Level: {p['premium_level']}\n🎒 Items: {items_owned}"
        )

    if text.startswith(",daily"):
        if "last_daily" in p and p["last_daily"] == now.date().isoformat():
            return await update.message.reply_text("🎁 Already claimed today's reward!")
        p["credits"] += 50
        p["energy"] += 20
        p["last_daily"] = now.date().isoformat()
        return await update.message.reply_text("🎁 +50 credits and +20 energy awarded!")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚡ Usage: ,mine ore <amount>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("❌ Invalid mining count.")
        if p["energy"] < count * 5:
            return await update.message.reply_text("⚡ Not enough energy.")
        ore_gain = 20 * count
        credit_gain = 10 * count
        p["ore"] += ore_gain
        p["energy"] -= count * 5
        p["credits"] += credit_gain
        return await update.message.reply_text(f"⛏️ Mined {ore_gain} ore, earned {credit_gain} credits!")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚙️ Usage: ,forge <unit> <amount>")
        unit, amount = parts[1], int(parts[2])
        if unit not in unit_types:
            return await update.message.reply_text(f"⚙️ Invalid unit. Available: {', '.join(unit_types)}")
        cost_ore = {"scout": 10, "tank": 30, "drone": 15}[unit]
        cost_credits = {"scout": 5, "tank": 20, "drone": 10}[unit]
        if p["ore"] < cost_ore * amount or p["credits"] < cost_credits * amount:
            return await update.message.reply_text("⚠️ Not enough resources.")
        p["ore"] -= cost_ore * amount
        p["credits"] -= cost_credits * amount
        p["army"][unit] += amount
        return await update.message.reply_text(f"🛠️ Forged {amount} {unit}(s).")

    if text.startswith(",map"):
        out = "🗺️ Zone Control Map:\n"
        for z, owner in zones.items():
            owner_name = players.get(owner, {}).get("name", "Unclaimed")
            out += f"{z}: {owner_name}\n"
        return await update.message.reply_text(out)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏰 Usage: ,claim <zone>")
        zone = parts[1]
        if zone not in zones:
            return await update.message.reply_text("⚠️ Invalid zone.")
        if p["credits"] < 100:
            return await update.message.reply_text("💳 Need 100 credits to claim.")
        zones[zone] = cid
        p["zone"] = zone
        p["credits"] -= 100
        return await update.message.reply_text(f"🏰 Zone {zone} claimed!")

    if text.startswith(",store"):
        out = "🏪 Store Packages:\n"
        for name, data in store_packages.items():
            out += f"- {name} ({data['price']} credits): {data['desc']}\n"
        return await update.message.reply_text(out)

    if text.startswith(",buy "):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buy <package>")
        pkg = parts[1]
        if pkg in store_packages:
            price = store_packages[pkg]["price"]
            if p["credits"] < price:
                return await update.message.reply_text("⚠️ Not enough credits.")
            p["credits"] -= price
            p["premium_spent"] += price
            update_premium_level(p)
            return await update.message.reply_text(f"✅ Purchased {pkg}!")
        else:
            return await update.message.reply_text("❓ Package not found.")

    if text.startswith(",blackmarket"):
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("🔒 Black Market locked. Use ,unlockbm first!")
        out = "🛒 Black Market Items:\n"
        for name, data in blackmarket_items.items():
            out += f"- {name} ({data['price']} credits) [{data['rarity']}]\n"
        return await update.message.reply_text(out)

    if text.startswith(",unlockbm"):
        if p["blackmarket_unlocked"]:
            return await update.message.reply_text("✅ Already unlocked.")
        if p["credits"] < 500:
            return await update.message.reply_text("💳 Need 500 credits to unlock.")
        p["credits"] -= 500
        p["blackmarket_unlocked"] = True
        return await update.message.reply_text("🎉 Black Market access granted!")

    if text.startswith(",buybm "):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buybm <item>")
        item = parts[1]
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("🔒 Unlock Black Market first.")
        if item not in blackmarket_items:
            return await update.message.reply_text("❓ Item not found.")
        price = blackmarket_items[item]["price"]
        if p["credits"] < price:
            return await update.message.reply_text("⚠️ Not enough credits.")
        p["credits"] -= price
        p["items"][item] = p["items"].get(item, 0) + 1
        return await update.message.reply_text(f"✅ Bought {item}.")

    if text.startswith(",premium"):
        return await update.message.reply_text(
            f"🏆 Premium Level: {p['premium_level']}\n"
            f"Total Credits Spent: {p['premium_spent']}"
        )

    await update.message.reply_text("❓ Unknown command. Type ,start or ,help.")

def update_premium_level(p):
    spent = p["premium_spent"]
    if spent >= 1000:
        p["premium_level"] = 3
    elif spent >= 500:
        p["premium_level"] = 2
    elif spent >= 200:
        p["premium_level"] = 1

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
