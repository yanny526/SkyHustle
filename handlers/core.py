from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, date
from sheet import get_sheet
import json

# Connect to Google Sheet
players_sheet = get_sheet().worksheet("SkyHustle")  # Make sure this tab exists

# Load or create player
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2  # row + header
            row["Army"] = json.loads(row.get("Army", '{"scout":0,"tank":0,"drone":0}'))
            row["Items"] = json.loads(row.get("Items", '{}'))
            return row

    # New Player Creation
    new_player = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": {"scout": 0, "tank": 0, "drone": 0},
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": "",
        "Faction": "",
        "Items": {},
    }
    players_sheet.append_row([
        new_player["ChatID"], new_player["Name"], new_player["Ore"], new_player["Energy"], new_player["Credits"],
        json.dumps(new_player["Army"]), new_player["Zone"], new_player["ShieldUntil"],
        new_player["DailyStreak"], new_player["LastDaily"], new_player["Faction"], json.dumps(new_player["Items"])
    ])
    new_player["_row"] = len(records) + 2
    return new_player

# Save updated player
def update_player(p):
    players_sheet.update(f"A{p['_row']}:L{p['_row']}", [[
        p["ChatID"],
        p["Name"],
        p["Ore"],
        p["Energy"],
        p["Credits"],
        json.dumps(p["Army"]),
        p["Zone"],
        p["ShieldUntil"],
        p["DailyStreak"],
        p["LastDaily"],
        p["Faction"],
        json.dumps(p["Items"])
    ]])

# Handle messages
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        intro = (
            "🌌 Welcome to SkyHustle!\n"
            "Set your callsign with ,name <alias>\n"
            "Check your status with ,status\n"
            "Mine ore with ,mine ore 1\n"
            "Forge army with ,forge scout 1\n"
            "Good luck, Commander!"
        )
        return await update.message.reply_text(intro)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}.")

    if text.startswith(",status"):
        army = p["Army"]
        items = p.get("Items", {})
        shield = p["ShieldUntil"] if p["ShieldUntil"] else "None"
        msg = (
            f"📊 {p['Name'] or 'Commander'}\n"
            f"🪨 Ore: {p['Ore']}  ⚡ Energy: {p['Energy']}  💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"🎒 Items: {items}\n"
            f"📍 Zone: {p['Zone'] or 'None'}  🛡️ Shield: {shield}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("Already claimed daily today.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        streak = int(p["DailyStreak"])
        p["Credits"] += 50
        p["Energy"] += 25
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 +50 credits, +25 energy. Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("Count must be a number.")
        if p["Energy"] < count * 5:
            return await update.message.reply_text("Not enough energy.")
        p["Ore"] += 20 * count
        p["Credits"] += 10 * count
        p["Energy"] -= count * 5
        update_player(p)
        return await update.message.reply_text(f"⛏️ Mined {20*count} ore. +{10*count} credits!")

    await update.message.reply_text("❓ Unknown command. Use ,start or ,status.")

