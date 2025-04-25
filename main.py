# SkyHustle Final Polished Main.py

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
from sheet import get_sheet
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Connect to Google Sheet
players_sheet = get_sheet().worksheet("SkyHustle")

# ------------------------ PLAYER SYSTEM ------------------------
def get_player(cid):
    records = players_sheet.get_all_records()

    if not records:
        records = []

    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row

    # Create new player if not found
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

def update_player(p):
    values = [
        p["ChatID"],
        p["Name"],
        p["Ore"],
        p["Energy"],
        p["Credits"],
        p["Army"],
        p["Zone"],
        p["ShieldUntil"],
        p["DailyStreak"],
        p["LastDaily"]
    ]
    players_sheet.update(f"A{p['_row']}:J{p['_row']}", [values])

# ------------------------ COMMAND HANDLER ------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    now = datetime.now()
    today = date.today()

    p = get_player(cid)

    if text.startswith(",start"):
        intro = (
            "🌌 Welcome to SkyHustle!\n"
            "Centuries from now, Hyperion’s core pulses with raw energy. "
            "As a fledgling Commander, you must mine ore, forge armies, "
            "build bases, and conquer zones.\n\n"
            "🔹 Set your callsign: ,name <alias>\n"
            "🔹 View stats: ,status\n"
            "🔹 Begin mining: ,mine ore 1\n"
            "🔹 Check missions: ,missions\n\n"
            "Forge your legend!"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        status = (
            f"📊 {p['Name'] or 'Commander'} Status:\n"
            f"🪨 Ore: {p['Ore']} | ⚡ Energy: {p['Energy']} | 💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"📍 Zone: {p['Zone'] or 'None'}"
        )
        return await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today's daily reward.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        streak = int(p["DailyStreak"])
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 25
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 +50 Credits, +25 Energy. Streak: {p['DailyStreak']} days!")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠ Usage: ,mine ore <amount>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Amount must be a number.")

        if int(p["Energy"]) < count * 5:
            return await update.message.reply_text("⚡ Not enough energy.")

        ore_gain = 20 * count
        credit_gain = 10 * count
        p["Ore"] = int(p["Ore"]) + ore_gain
        p["Credits"] = int(p["Credits"]) + credit_gain
        p["Energy"] = int(p["Energy"]) - count * 5
        update_player(p)
        return await update.message.reply_text(f"⛏ You mined {ore_gain} ore and earned {credit_gain} credits.")

    if text.startswith(",map"):
        return await update.message.reply_text("🗺️ Map system coming soon!")

    if text.startswith(",forge"):
        return await update.message.reply_text("⚒️ Forge system coming soon!")

    if text.startswith(",missions"):
        return await update.message.reply_text("🎯 Missions coming soon!")

    if text.startswith(",blackmarket"):
        return await update.message.reply_text("🛒 Black Market access coming soon!")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "🛠️ Commands:\n"
            ",start | ,name <alias> | ,status | ,daily | ,mine ore <amount>\n"
            ",map | ,forge | ,missions | ,blackmarket"
        )

    await update.message.reply_text("❓ Unknown command. Use ,help")

# ------------------------ INIT BOT ------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
