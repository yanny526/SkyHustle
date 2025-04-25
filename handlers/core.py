from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, date
from sheet import get_sheet
import json

# Connect to Google Sheet tab
players_sheet = get_sheet().worksheet("SkyHustle")  # Match your tab name

# Load or create player
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2  # Row index in sheet
            return row

    # New player structure
    new_player = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": json.dumps({"scout": 0, "tank": 0, "drone": 0}),
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": ""
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

# Push player to sheet
def update_player(p):
    players_sheet.update(
        f"A{p['_row']}:J{p['_row']}",
        [[
            p["ChatID"],
            p["Name"],
            int(p["Ore"]),
            int(p["Energy"]),
            int(p["Credits"]),
            p["Army"],
            p["Zone"],
            p["ShieldUntil"],
            p["DailyStreak"],
            p["LastDaily"]
        ]]
    )

# Handle incoming message
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    # Intro
    if text.startswith(",start"):
        intro = (
            "🌌 Welcome to SkyHustle!\n"
            "Centuries from now, Hyperion’s core pulses with raw energy. "
            "As a fledgling Commander, you must mine ore, bolster defenses, "
            "and conquer rivals to claim the stars.\n\n"
            "🔹 Set your callsign: ,name <alias>\n"
            "🔹 View stats: ,status\n"
            "🔹 Begin mining: ,mine ore 1\n\n"
            "Forge your legend!"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    # Set player name
    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    # View player status
    if text.startswith(",status"):
        army = json.loads(p["Army"])
        msg = (
            f"📊 {p['Name'] or 'Commander'} Status:\n"
            f"🪨 Ore: {p['Ore']}  ⚡ Energy: {p['Energy']}  💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"📍 Zone: {p['Zone'] or 'None'}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # Claim daily reward
    if text.startswith(",daily"):
        last_daily = None
        try:
            last_daily = datetime.strptime(p["LastDaily"], "%Y-%m-%d").date() if p["LastDaily"] else None
        except:
            last_daily = None

        if str(p["LastDaily"]) == str(today):
            return await update.message.reply_text("🎁 Already claimed today.")

        streak = int(p["DailyStreak"])
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 25
        p["DailyStreak"] = streak + 1 if last_daily == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 +50 credits, +25 energy. Streak: {p['DailyStreak']} days.")

    # Mine ore
    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1].lower() != "ore":
            return await update.message.reply_text("⚠ Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Count must be a number.")
        
        energy = int(p["Energy"])
        if energy < count * 5:
            return await update.message.reply_text("⚠ Not enough energy.")
        
        ore_gain = 20 * count
        credit_gain = 10 * count
        p["Ore"] = int(p["Ore"]) + ore_gain
        p["Energy"] = energy - (count * 5)
        p["Credits"] = int(p["Credits"]) + credit_gain
        update_player(p)
        return await update.message.reply_text(f"⛏ Mined {ore_gain} ore. +{credit_gain} credits!")

    # Unknown fallback
    return await update.message.reply_text("❓ Unknown command. Type ,start or ,status.")
