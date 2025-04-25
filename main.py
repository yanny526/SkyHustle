# SkyHustle - Full Up to Phase 8 (Mining, Items, PvP)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os, json

from sheet import get_sheet
from utils import find_by_name

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

players_sheet = get_sheet().worksheet("SkyHustle")  # Update if your tab name changes

item_defs = {
    "infinityscout1": {"type": "perishable", "desc": "Advanced scout (1 use)"},
    "reviveall": {"type": "perishable", "desc": "Revives all regular units and buildings"},
    "hazmat": {"type": "passive", "desc": "Access Radiation Zones"},
}

zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}
unit_types = ["scout", "drone", "tank"]

# -- Helpers --
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row

    new_player = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": json.dumps({u: 0 for u in unit_types}),
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": "",
        "Items": json.dumps({})
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
        p["LastDaily"],
        p["Items"]
    ]
    players_sheet.update(f"A{p['_row']}:J{p['_row']}", [values])

def give_item(p, item_id):
    items = json.loads(p["Items"])
    items.setdefault(item_id, 0)
    items[item_id] += 1
    p["Items"] = json.dumps(items)
    update_player(p)

def use_item(p, item_id):
    items = json.loads(p["Items"])
    if item_id not in item_defs:
        return False, "❌ Invalid item."
    if items.get(item_id, 0) <= 0:
        return False, "❌ You don't own this item."
    if item_defs[item_id]["type"] == "perishable":
        items[item_id] -= 1
        if items[item_id] == 0:
            del items[item_id]
    p["Items"] = json.dumps(items)
    update_player(p)
    return True, f"✅ Used item: {item_id}"

# -- Main Handler --
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        intro = (
            "🌌 Welcome to SkyHustle!\n"
            "Mine ore, build armies, and dominate zones!\n\n"
            "🔹 Set your callsign: ,name <alias>\n"
            "🔹 View stats: ,status\n"
            "🔹 Start mining: ,mine ore 1\n"
            "🔹 Battle rivals: ,attack <name>"
        )
        return await update.message.reply_text(intro)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠ Usage: ,name <alias>")
        ocid, _ = find_by_name(alias, {int(r["ChatID"]): r for r in players_sheet.get_all_records()})
        if ocid and ocid != cid:
            return await update.message.reply_text("⚠ Alias taken.")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to {alias}!")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p["Items"])
        shield = p["ShieldUntil"]
        shield_str = shield if shield else "None"
        msg = (
            f"📊 {p['Name'] or 'Commander'} Status:\n"
            f"🪨 Ore: {p['Ore']} ⚡ Energy: {p['Energy']} 💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"🎒 Items: {items}\n"
            f"🛡 Shield: {shield_str}\n"
            f"📍 Zone: {p['Zone'] or 'None'}"
        )
        return await update.message.reply_text(msg)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        streak = int(p["DailyStreak"])
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 25
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 +50 credits, +25 energy. Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠ Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Count must be a number.")
        if int(p["Energy"]) < count * 5:
            return await update.message.reply_text("⚠ Not enough energy.")
        ore_gain = 20 * count
        credit_gain = 10 * count
        p["Ore"] = int(p["Ore"]) + ore_gain
        p["Energy"] = int(p["Energy"]) - count * 5
        p["Credits"] = int(p["Credits"]) + credit_gain
        update_player(p)
        return await update.message.reply_text(f"⛏ Mined {ore_gain} ore. +{credit_gain} credits!")

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3 or parts[1] not in unit_types:
            return await update.message.reply_text("⚙ Usage: ,forge <unit> <count>")
        unit, amt = parts[1], int(parts[2])
        cost = {"scout": (10, 5), "drone": (15, 10), "tank": (30, 20)}[unit]
        if int(p["Ore"]) < cost[0] * amt or int(p["Credits"]) < cost[1] * amt:
            return await update.message.reply_text("⚠ Not enough ore or credits.")
        army = json.loads(p["Army"])
        army[unit] += amt
        p["Ore"] = int(p["Ore"]) - cost[0] * amt
        p["Credits"] = int(p["Credits"]) - cost[1] * amt
        p["Army"] = json.dumps(army)
        update_player(p)
        return await update.message.reply_text(f"⚙ Forged {amt} {unit}(s)!")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚙ Usage: ,use <item>")
        success, msg = use_item(p, parts[1])
        return await update.message.reply_text(msg)

    if text.startswith(",map"):
        out = "🌍 Zone Control:\n"
        for z, o in zones.items():
            name = o if o else "Unclaimed"
            out += f"{z}: {name}\n"
        return await update.message.reply_text(out)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in zones:
            return await update.message.reply_text("⚙ Usage: ,claim <zone>")
        if int(p["Credits"]) < 100:
            return await update.message.reply_text("⚠ Need 100 credits.")
        zones[parts[1]] = p["Name"]
        p["Zone"] = parts[1]
        p["Credits"] = int(p["Credits"]) - 100
        update_player(p)
        return await update.message.reply_text(f"✅ You now control {parts[1]}.")

    if text.startswith(",missions"):
        return await update.message.reply_text("🎯 Mission system coming soon.")

    if text.startswith(",scout"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,scout <playername>")
        target_name = parts[1]
        records = players_sheet.get_all_records()
        tcid, tp = find_by_name(target_name, {int(r["ChatID"]): r for r in records})
        if not tp:
            return await update.message.reply_text("❌ Player not found.")
        if tp["ShieldUntil"]:
            return await update.message.reply_text(f"🛡 {target_name} is shielded.")
        army = json.loads(tp["Army"])
        return await update.message.reply_text(
            f"🕵 Scout report for {tp['Name']}:\n"
            f"Ore: {tp['Ore']} | Energy: {tp['Energy']} | Credits: {tp['Credits']}\n"
            f"Army: {army}"
        )

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,attack <playername>")
        target_name = parts[1]
        records = players_sheet.get_all_records()
        tcid, tp = find_by_name(target_name, {int(r["ChatID"]): r for r in records})
        if not tp:
            return await update.message.reply_text("❌ Player not found.")
        if tp["ShieldUntil"]:
            return await update.message.reply_text(f"🛡 {target_name} is shielded.")

        my_army = json.loads(p["Army"])
        their_army = json.loads(tp["Army"])
        my_power = my_army.get("scout", 0) * 5 + my_army.get("drone", 0) * 10 + my_army.get("tank", 0) * 20
        their_power = their_army.get("scout", 0) * 5 + their_army.get("drone", 0) * 10 + their_army.get("tank", 0) * 20

        result = "win" if my_power >= their_power else "lose"

        if result == "win":
            steal_ore = min(20, int(tp["Ore"]))
            steal_credits = min(10, int(tp["Credits"]))
            p["Ore"] = int(p["Ore"]) + steal_ore
            p["Credits"] = int(p["Credits"]) + steal_credits
            tp["Ore"] = int(tp["Ore"]) - steal_ore
            tp["Credits"] = int(tp["Credits"]) - steal_credits
            msg = f"⚔ Victory!\nStolen {steal_ore} ore and {steal_credits} credits."
        else:
            msg = "💥 Defeat! You lost the battle."

        p["ShieldUntil"] = ""
        tp["ShieldUntil"] = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        update_player(p)
        update_player(tp)

        return await update.message.reply_text(msg)

    if text.startswith(",help"):
        return await update.message.reply_text(
            "Commands: ,start ,name ,status ,daily ,mine ,forge ,use ,map ,claim ,missions ,scout ,attack"
        )

    await update.message.reply_text("❓ Unknown command. Type ,help")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
