# SkyHustle Full Game Final Version (Phases 1-56 Complete)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os
import json
import gspread
from google.oauth2.service_account import Credentials
import base64

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"

def get_sheet():
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_BASE64")).decode("utf-8")
    creds_dict = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit")

players_sheet = get_sheet().worksheet("SkyHustle")

# ---------------- GLOBALS ----------------
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "infinityscout2": {"type": "perishable", "desc": "Advanced scout (Level 2, 1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all units & buildings except Black Market units"},
    "hazmat": {"type": "passive", "desc": "Allows access to Radiation Zones"},
    "emppulse": {"type": "perishable", "desc": "EMP attack disables opponent defense 24h"},
    "shieldboost": {"type": "perishable", "desc": "Auto-absorbs 1 attack today"},
}
base_unit_costs = {"scout": (10,5), "tank": (30,20), "drone": (15,10)}
unit_types = ["scout", "tank", "drone"]

# ---------------- HELPERS ----------------
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row

    # If not found, create
    new_player = {
        "ChatID": cid, "Name": "", "Ore": 0, "Energy": 100, "Credits": 100,
        "Army": json.dumps({"scout":0, "tank":0, "drone":0}), "Zone": "",
        "ShieldUntil": "", "DailyStreak": 0, "LastDaily": "",
        "BlackMarketUnlocked": "No", "Items": json.dumps({})
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

def update_player(p):
    players_sheet.update(f"A{p['_row']}:K{p['_row']}", [[
        p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"],
        p["Army"], p["Zone"], p["ShieldUntil"], p["DailyStreak"], p["LastDaily"],
        p["BlackMarketUnlocked"], p["Items"]
    ]])

def save_player(p):
    update_player(p)

def find_by_name(alias):
    records = players_sheet.get_all_records()
    for i, p in enumerate(records):
        if p["Name"].lower() == alias.lower():
            return i + 2, p
    return None, None

# ---------------- COMMANDS ----------------
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    now = datetime.now()
    today = date.today()

    p = get_player(cid)

    if text.startswith(",start"):
        return await update.message.reply_text("🌌 SkyHustle launched! Use ,name to begin!")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        save_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items_owned = ", ".join([f"{k}x{v}" for k,v in json.loads(p["Items"]).items()]) or "None"
        return await update.message.reply_text(
            f"📊 {p['Name']}:\n"
            f"🪨 Ore: {p['Ore']} ⚡Energy: {p['Energy']} 💳Credits: {p['Credits']}\n"
            f"Army: {army}\nItems: {items_owned}\nZone: {p['Zone'] or 'None'}", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today.")
        streak = int(p["DailyStreak"])
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 20
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        save_player(p)
        return await update.message.reply_text(f"🎁 +50 credits, +20 energy! Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠ Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("⚠ Count must be number.")
        if int(p["Energy"]) < count * 5:
            return await update.message.reply_text("⚡ Not enough energy.")
        ore_gain = 20 * count
        p["Ore"] = int(p["Ore"]) + ore_gain
        p["Energy"] = int(p["Energy"]) - count * 5
        p["Credits"] = int(p["Credits"]) + 10*count
        save_player(p)
        return await update.message.reply_text(f"⛏️ You mined {ore_gain} ore. +{10*count} credits.")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚠ Usage: ,forge <unit> <amount>")
        unit, amt = parts[1], int(parts[2])
        if unit not in unit_types:
            return await update.message.reply_text("⚠ Invalid unit.")
        ore_cost, credit_cost = base_unit_costs[unit]
        total_ore = ore_cost * amt
        total_credits = credit_cost * amt
        if int(p["Ore"]) < total_ore or int(p["Credits"]) < total_credits:
            return await update.message.reply_text("⚠ Not enough resources.")
        army = json.loads(p["Army"])
        army[unit] += amt
        p["Ore"] = int(p["Ore"]) - total_ore
        p["Credits"] = int(p["Credits"]) - total_credits
        p["Army"] = json.dumps(army)
        save_player(p)
        return await update.message.reply_text(f"⚙️ Forged {amt} {unit}(s)!")

    if text.startswith(",unlockblackmarket"):
        if p["BlackMarketUnlocked"] == "Yes":
            return await update.message.reply_text("🛒 Already unlocked!")
        if int(p["Credits"]) < 500:
            return await update.message.reply_text("💳 Need 500 credits to unlock Black Market!")
        p["Credits"] = int(p["Credits"]) - 500
        p["BlackMarketUnlocked"] = "Yes"
        save_player(p)
        return await update.message.reply_text("✅ Black Market unlocked!")

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,buy <item>")
        if p["BlackMarketUnlocked"] != "Yes":
            return await update.message.reply_text("❌ Unlock Black Market first!")
        item = parts[1]
        if item not in item_defs:
            return await update.message.reply_text("⚠ Invalid item.")
        item_cost = {
            "infinityscout1": 100,
            "infinityscout2": 250,
            "reviveall": 500,
            "hazmat": 300,
            "emppulse": 200,
            "shieldboost": 150
        }.get(item, 999)
        if int(p["Credits"]) < item_cost:
            return await update.message.reply_text("❌ Not enough credits.")
        items = json.loads(p["Items"])
        items.setdefault(item, 0)
        items[item] += 1
        p["Credits"] = int(p["Credits"]) - item_cost
        p["Items"] = json.dumps(items)
        save_player(p)
        return await update.message.reply_text(f"✅ Purchased {item}!")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,use <item>")
        items = json.loads(p["Items"])
        item = parts[1]
        if item not in items or items[item] == 0:
            return await update.message.reply_text("❌ You don't own this item.")
        if item_defs[item]["type"] == "perishable":
            items[item] -= 1
            if items[item] <= 0:
                del items[item]
        p["Items"] = json.dumps(items)
        save_player(p)
        return await update.message.reply_text(f"✅ Used {item}.")

    await update.message.reply_text("❓ Unknown command. Type ,start or ,status.")

# ---------------- BOOT ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
