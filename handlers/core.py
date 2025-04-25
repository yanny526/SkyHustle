from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime
from sheet import get_sheet
import json

# Connect to the sheet
players_sheet = get_sheet().worksheet("Sheet1")  # Change to your actual sheet tab name if needed

# Load player or add if not found
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2  # Google Sheets rows start at 1, headers at row 1
            return row

    # New player data
    new_player = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 0,
        "Army": '{"scout":0,"tank":0,"drone":0}',
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": ""
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

# Update a player in the sheet
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

# Handle Telegram messages
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()

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

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        msg = (
            f"📊 {p['Name'] or 'Commander'} Status:\n"
            f"🪨 Ore: {p['Ore']}  ⚡ Energy: {p['Energy']}  💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"📍 Zone: {p['Zone'] or 'None'}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    await update.message.reply_text("❓ Unknown command. Type ,start or ,status.")
