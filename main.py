# SkyHustle - Final Optimized Engine (Phase 1-56)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta, date
from sheet import get_sheet
import json
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
players_sheet = get_sheet().worksheet("SkyHustle")

unit_types = ["scout", "tank", "drone"]
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
black_market_unlock_price = 500
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)", "price": 250},
    "infinityscout2": {"type": "perishable", "desc": "Elite scout (1 use)", "price": 400},
    "reviveall": {"type": "perishable", "desc": "Revives all non-Black Market units", "price": 500},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones", "price": 300},
    "emp": {"type": "perishable", "desc": "Disable opponent defenses", "price": 200},
    "advancedshield": {"type": "passive", "desc": "Auto-absorb 1st attack daily", "price": 350}
}

def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row
    new_player = {
        "ChatID": cid, "Name": "", "Ore": 0, "Energy": 100, "Credits": 100,
        "Army": json.dumps({u: 0 for u in unit_types}), "Zone": "",
        "ShieldUntil": "", "DailyStreak": 0, "LastDaily": "",
        "Items": json.dumps({}), "BMUnlocked": "False"
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

def update_player(p):
    players_sheet.update(
        f"A{p['_row']}:L{p['_row']}",
        [[p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"], p["Army"],
          p["Zone"], p["ShieldUntil"], p["DailyStreak"], p["LastDaily"],
          p.get("Items", json.dumps({})), p.get("BMUnlocked", "False")]]
    )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    today = date.today()
    now = datetime.now()

    if text.startswith(",start"):
        return await update.message.reply_text(
            "🌌 Welcome to SkyHustle! Use ,name <alias> to begin.", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p.get("Items", "{}"))
        shield_time = p["ShieldUntil"] if p["ShieldUntil"] else "None"
        return await update.message.reply_text(
            f"📊 {p['Name'] or 'Commander'}\n"
            f"🪨 Ore: {p['Ore']} | ⚡ Energy: {p['Energy']} | 💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"🎒 Items: {items}\n"
            f"🛡 Shield: {shield_time}\n"
            f"📍 Zone: {p['Zone'] or 'None'}", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today!")
        p["Credits"] += 50
        p["Energy"] += 25
        p["DailyStreak"] = p["DailyStreak"] + 1 if p["LastDaily"] == str(today - timedelta(days=1)) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 +50 credits, +25 energy. Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore": return await update.message.reply_text("⚠ Usage: ,mine ore <count>")
        try: count = int(parts[2])
        except: return await update.message.reply_text("⚠ Count must be a number.")
        if p["Energy"] < count * 5: return await update.message.reply_text("⚡ Not enough energy!")
        ore_gain = 20 * count
        p["Ore"] += ore_gain
        p["Energy"] -= count * 5
        p["Credits"] += 10 * count
        update_player(p)
        return await update.message.reply_text(f"⛏ Mined {ore_gain} ore and earned {10*count} credits!")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types: return await update.message.reply_text("⚠ Usage: ,forge <unit> <count>")
        unit, amt = parts[1], int(parts[2])
        army = json.loads(p["Army"])
        ore_cost = 10 * amt
        credit_cost = 5 * amt
        if p["Ore"] < ore_cost or p["Credits"] < credit_cost:
            return await update.message.reply_text("⚠ Insufficient resources!")
        p["Ore"] -= ore_cost
        p["Credits"] -= credit_cost
        army[unit] += amt
        p["Army"] = json.dumps(army)
        update_player(p)
        return await update.message.reply_text(f"🛡 Forged {amt} {unit}(s)!")

    if text.startswith(",blackmarket"):
        if p.get("BMUnlocked", "False") == "False":
            return await update.message.reply_text(
                f"🔒 Black Market locked. Unlock for {black_market_unlock_price} credits using ,unlockbm")
        items_list = "\n".join([f"{k}: {v['desc']} (Cost: {v['price']})" for k,v in item_defs.items()])
        return await update.message.reply_text(f"🖤 Black Market Items:\n{items_list}")

    if text.startswith(",unlockbm"):
        if p.get("BMUnlocked", "False") == "True":
            return await update.message.reply_text("🖤 Already unlocked Black Market.")
        if p["Credits"] < black_market_unlock_price:
            return await update.message.reply_text("💳 Not enough credits!")
        p["Credits"] -= black_market_unlock_price
        p["BMUnlocked"] = "True"
        update_player(p)
        return await update.message.reply_text("🖤 Black Market unlocked! Use ,blackmarket to view items.")

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2: return await update.message.reply_text("⚠ Usage: ,buy <item>")
        item = parts[1]
        if item not in item_defs:
            return await update.message.reply_text("⚠ Invalid item.")
        if p.get("BMUnlocked", "False") == "False":
            return await update.message.reply_text("🔒 Black Market access required!")
        price = item_defs[item]["price"]
        if p["Credits"] < price:
            return await update.message.reply_text("💳 Not enough credits.")
        p["Credits"] -= price
        items = json.loads(p.get("Items", "{}"))
        items[item] = items.get(item, 0) + 1
        p["Items"] = json.dumps(items)
        update_player(p)
        return await update.message.reply_text(f"🖤 Purchased {item}!")

    if text.startswith(",map"):
        out = "🌍 Zone Control:\n"
        for z, o in zones.items():
            out += f"{z}: {o or 'Unclaimed'}\n"
        return await update.message.reply_text(out)

    if text.startswith(",help"):
        return await update.message.reply_text(
            "📚 Commands:\n"
            ",start ,name <alias> ,status ,daily ,mine ore <count> ,forge <unit> <count>\n"
            ",blackmarket ,unlockbm ,buy <item> ,map", parse_mode=ParseMode.MARKDOWN)

    await update.message.reply_text("❓ Unknown command. Type ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
