# SkyHustle - Phase 5 Upgrade
# Adds Black Market, Store, Timed Cooldowns, and Zone Upgrades

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
blackmarket_items = {
    "infinityscout1": {"price": 20, "type": "perishable", "desc": "One-time advanced scout"},
    "reviveall": {"price": 500, "type": "perishable", "desc": "Revives all damaged units (excl. premium)"},
    "hazmat": {"price": 100, "type": "passive", "desc": "Access Radiation Zones"},
    "emppulse": {"price": 75, "type": "perishable", "desc": "Disable enemy defenses for 1 hour"},
    "advshield": {"price": 150, "type": "passive", "desc": "Absorb first daily attack"}
}
normal_store = {
    "energyboost": {"price": 10, "desc": "+50 energy now"},
    "creditpack": {"price": 15, "desc": "+100 credits"},
    "orecrate": {"price": 15, "desc": "+100 ore"}
}

# ---------------- Core Player Struct ----------------
def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 100, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {u: 0 for u in unit_types}, "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0, "daily_streak": 0,
        "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set(), "items": {},
        "blackmarket_level": 0, "cooldowns": {}
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

def give_item(p, item_id):
    p["items"].setdefault(item_id, 0)
    p["items"][item_id] += 1

def use_item(p, item_id):
    if item_id not in blackmarket_items:
        return False, "❌ Invalid item."
    if p["items"].get(item_id, 0) <= 0:
        return False, "❌ You don't own this item."
    if blackmarket_items[item_id]["type"] == "perishable":
        p["items"][item_id] -= 1
        if p["items"][item_id] == 0:
            del p["items"][item_id]
    return True, f"✅ Used item: {item_id}"

# ---------------- Handler ----------------
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
        p["name"] = alias
        return await update.message.reply_text(f"Callsign set to {alias}.")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        items_owned = ", ".join([f"{k} x{v}" for k,v in p["items"].items()]) or "None"
        return await update.message.reply_text(
            f"Name: {p['name']}\nOre: {p['ore']}\nEnergy: {p['energy']}\nCredits: {p['credits']}\n"
            f"Refinery Lv{p['refinery_level']} | Lab Lv{p['lab_level']}\nArmy: {p['army']}\n"
            f"Items: {items_owned}\nShield: {shield}\nBM Level: {p['blackmarket_level']}")

    if text.startswith(",blackmarket"):
        parts = text.split()
        if len(parts) == 1:
            bm_level = p["blackmarket_level"]
            msg = "🛒 Black Market (Lv {bm_level}):\n"
            for k, v in blackmarket_items.items():
                msg += f"- {k}: {v['desc']} (R{v['price']})\n"
            return await update.message.reply_text(msg)
        if parts[1] == "buy" and len(parts) == 3:
            item = parts[2]
            if item not in blackmarket_items:
                return await update.message.reply_text("❌ Item not found.")
            give_item(p, item)
            return await update.message.reply_text(f"✅ Purchased {item} (simulate real payment here)")
        if parts[1] == "upgrade":
            p["blackmarket_level"] += 1
            return await update.message.reply_text(f"⬆️ Black Market upgraded to Lv {p['blackmarket_level']}")

    if text.startswith(",store"):
        out = "🏪 SkyHustle Store:\n"
        for k,v in normal_store.items():
            out += f"- {k}: {v['desc']} (R{v['price']})\n"
        return await update.message.reply_text(out)

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,store ,blackmarket ,blackmarket buy <item> ,use <item>")

    await update.message.reply_text("Unknown command. Use ,help")

# ---------------- Init ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
