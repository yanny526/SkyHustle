# SkyHustle - Phase 31-32 Fusion Update
# Black Market Rework + Premium Simulation

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
    
    if text.startswith(",start"):
        return await update.message.reply_text("🌌 SkyHustle launched! Use ,name <alias> to start.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        p["name"] = alias
        return await update.message.reply_text(f"🚀 Callsign set to {alias}")

    if text.startswith(",status"):
        bm = "Unlocked" if p["blackmarket_unlocked"] else "Locked"
        return await update.message.reply_text(
            f"👤 {p['name']}\n🪨 Ore: {p['ore']} | ⚡ Energy: {p['energy']} | 💳 Credits: {p['credits']}\n"
            f"🛒 BlackMarket: {bm} | 🏆 Premium Level: {p['premium_level']}"
        )

    if text.startswith(",store"):
        out = "🏪 Store Packages:\n"
        for k, v in store_packages.items():
            out += f"- {k} ({v['price']} credits): {v['desc']}\n"
        return await update.message.reply_text(out)

    if text.startswith(",buy "):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buy <package>")
        pkg = parts[1]
        if pkg in store_packages:
            cost = store_packages[pkg]["price"]
            if p["credits"] < cost:
                return await update.message.reply_text("❌ Not enough credits.")
            p["credits"] -= cost
            p["premium_spent"] += cost
            check_premium_level(p)
            return await update.message.reply_text(f"✅ Purchased {pkg}. Thanks!")
        else:
            return await update.message.reply_text("❓ Package not found.")

    if text.startswith(",blackmarket"):
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("🔒 Black Market locked. Use ,unlockbm 500 credits.")
        out = "🛒 Black Market Items:\n"
        for k, v in blackmarket_items.items():
            out += f"- {k} ({v['price']} credits) [{v['rarity']}]\n"
        return await update.message.reply_text(out)

    if text.startswith(",unlockbm"):
        if p["blackmarket_unlocked"]:
            return await update.message.reply_text("✅ Already unlocked.")
        if p["credits"] < 500:
            return await update.message.reply_text("❌ Need 500 credits to unlock Black Market.")
        p["credits"] -= 500
        p["blackmarket_unlocked"] = True
        return await update.message.reply_text("🎉 Black Market unlocked!")

    if text.startswith(",buybm "):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buybm <item>")
        item = parts[1]
        if not p["blackmarket_unlocked"]:
            return await update.message.reply_text("🔒 Black Market locked.")
        if item in blackmarket_items:
            price = blackmarket_items[item]["price"]
            if p["credits"] < price:
                return await update.message.reply_text("❌ Not enough credits.")
            p["credits"] -= price
            p["items"][item] = p["items"].get(item, 0) + 1
            return await update.message.reply_text(f"✅ Bought {item}. Good luck!")
        else:
            return await update.message.reply_text("❓ Item not found.")

    if text.startswith(",premium"):
        msg = (
            f"🏆 Premium Level: {p['premium_level']}\n"
            f"🛍 Total Credits Spent: {p['premium_spent']}\n"
            f"💎 Benefits: Higher mining rate, cheaper Black Market soon!"
        )
        return await update.message.reply_text(msg)

    await update.message.reply_text("❓ Unknown command.")

def check_premium_level(p):
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
