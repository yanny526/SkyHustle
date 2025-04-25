# SkyHustle - Full Hyperdrive Game Engine (Phase 1-46)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta, date
import os, json, base64, gspread
from google.oauth2.service_account import Credentials

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit"

# --- GOOGLE SHEETS CONNECT ---
def get_sheet():
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_BASE64")).decode("utf-8")
    creds_dict = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    return client.open_by_url(SPREADSHEET_URL).worksheet("SkyHustle")

players_sheet = get_sheet()

# --- GAME DATA ---
unit_types = ["scout", "tank", "drone"]
item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "infinityscout2": {"type": "perishable", "desc": "Elite scout (1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
    "emppulse": {"type": "perishable", "desc": "EMP disables opponent defenses"},
    "advancedshield": {"type": "passive", "desc": "Absorbs first daily attack"}
}
zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
missions = {}

# --- HELPERS ---
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row
    new_player = {
        "ChatID": cid, "Name": "", "Ore": 0, "Energy": 100, "Credits": 100,
        "Army": json.dumps({u: 0 for u in unit_types}), "Zone": "", "ShieldUntil": "",
        "DailyStreak": 0, "LastDaily": "", "Items": json.dumps({}), "BlackMarketUnlocked": False,
        "Wins": 0, "Losses": 0, "Rank": 1000
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

def update_player(p):
    values = [
        p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"],
        p["Army"], p["Zone"], p["ShieldUntil"], p["DailyStreak"],
        p["LastDaily"], p["Items"], p.get("BlackMarketUnlocked", False),
        p.get("Wins", 0), p.get("Losses", 0), p.get("Rank", 1000)
    ]
    players_sheet.update(f"A{p['_row']}:O{p['_row']}", [values])

def use_item(p, item_id):
    items = json.loads(p["Items"])
    if item_id not in items or items[item_id] == 0:
        return False, "❌ You don't own this item."
    if item_defs[item_id]["type"] == "perishable":
        items[item_id] -= 1
        if items[item_id] == 0:
            del items[item_id]
    p["Items"] = json.dumps(items)
    update_player(p)
    return True, f"✅ Used {item_id}."

# --- CORE GAME LOGIC ---
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        return await update.message.reply_text("SkyHustle activated! Use ,name to begin.")

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p["Items"])
        msg = (
            f"📊 {p['Name']}\n"
            f"🪨 Ore: {p['Ore']} | ⚡ Energy: {p['Energy']} | 💳 Credits: {p['Credits']}\n"
            f"🏹 Army: {army}\n"
            f"🎒 Items: {items if items else 'None'}\n"
            f"📍 Zone: {p['Zone'] or 'None'} | 🛡️ Rank: {p['Rank']}"
        )
        return await update.message.reply_text(msg)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        p["Credits"] += 50
        p["Energy"] += 20
        p["DailyStreak"] = p["DailyStreak"] + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 Claimed: +50 Credits +20 Energy. Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚒ Usage: ,mine ore <amount>")
        try: amt = int(parts[2])
        except: return await update.message.reply_text("⚒ Amount must be a number.")
        if p["Energy"] < amt * 5:
            return await update.message.reply_text("⚠ Not enough Energy.")
        ore_gain = 20 * amt
        credit_gain = 10 * amt
        p["Ore"] += ore_gain
        p["Energy"] -= amt * 5
        p["Credits"] += credit_gain
        update_player(p)
        return await update.message.reply_text(f"⛏️ Mined {ore_gain} ore, +{credit_gain} credits!")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types:
            return await update.message.reply_text("⚒ Usage: ,forge <unit> <amount>")
        unit, amt = parts[1], int(parts[2])
        costs = {"scout": (10,5), "drone": (15,10), "tank": (30,20)}
        ore_cost, credit_cost = costs[unit]
        if p["Ore"] < ore_cost*amt or p["Credits"] < credit_cost*amt:
            return await update.message.reply_text("⚠ Insufficient Ore or Credits.")
        army = json.loads(p["Army"])
        army[unit] += amt
        p["Ore"] -= ore_cost*amt
        p["Credits"] -= credit_cost*amt
        p["Army"] = json.dumps(army)
        update_player(p)
        return await update.message.reply_text(f"🛠 Forged {amt} {unit}(s)!")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in zones:
            return await update.message.reply_text("Usage: ,claim <zone>")
        if p["Credits"] < 100:
            return await update.message.reply_text("⚠ Need 100 credits.")
        zones[parts[1]] = cid
        p["Zone"] = parts[1]
        p["Credits"] -= 100
        update_player(p)
        return await update.message.reply_text(f"🌍 You now control {parts[1]}!")

    if text.startswith(",missions"):
        return await update.message.reply_text("🎯 Missions: Coming soon!")

    if text.startswith(",blackmarket"):
        if not p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("🔒 Unlock Black Market for R50 payment.")
        out = "🛒 Black Market:\n"
        for k, v in item_defs.items():
            out += f"- {k}: {v['desc']}\n"
        return await update.message.reply_text(out)

    if text.startswith(",help"):
        return await update.message.reply_text("Commands: ,start ,name ,status ,daily ,mine ,forge ,use ,claim ,missions ,blackmarket")

    await update.message.reply_text("Unknown command. Use ,help")

# --- BOOT ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
