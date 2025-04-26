# SkyHustle Main Core - PART 1

import os
import json
from datetime import datetime, timedelta, date
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from sheet import get_sheet

# Connect to Google Sheet
players_sheet = get_sheet().worksheet("SkyHustle")

# Player Helpers
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row
    # Create new player
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
        "LastDaily": "",
        "BlackMarketUnlocked": "FALSE",
        "Items": json.dumps({})
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

def update_player(p):
    players_sheet.update(f"A{p['_row']}:L{p['_row']}", [[
        p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"],
        p["Army"], p["Zone"], p["ShieldUntil"], p["DailyStreak"],
        p["LastDaily"], p["BlackMarketUnlocked"], p["Items"]
    ]])

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        intro = (
            "🌌 *Welcome Commander!*\n\n"
            "In the ruins of Hyperion’s shattered worlds, factions rise and fall. "
            "You are the last hope.\n\n"
            "🔹 Set your identity: `,name <yourname>`\n"
            "🔹 View stats: `,status`\n"
            "🔹 Begin mining: `,mine ore 1`\n"
            "🔹 Claim daily rewards: `,daily`\n\n"
            "_Forge your destiny among the stars._ 🚀"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign registered as *{alias}*", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p["Items"])
        shield = p["ShieldUntil"] if p["ShieldUntil"] else "None"
        msg = (
            f"👤 *{p['Name'] or 'Unregistered Commander'}*\n"
            f"🪨 Ore: `{p['Ore']}` | ⚡ Energy: `{p['Energy']}` | 💳 Credits: `{p['Credits']}`\n"
            f"🛡 Shield: `{shield}` | 📍 Zone: `{p['Zone'] or 'None'}`\n"
            f"🤖 Army: `{army}`\n"
            f"🎒 Items: `{items}`"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        streak = int(p["DailyStreak"])
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 30
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 Claimed +50 Credits, +30 Energy! Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠ Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Count must be a number.")
        if p["Energy"] < count * 5:
            return await update.message.reply_text("⚠ Not enough energy.")
        ore_gain = 20 * count
        p["Ore"] += ore_gain
        p["Energy"] -= count * 5
        update_player(p)
        return await update.message.reply_text(f"⛏ Your miners recovered *{ore_gain} Ore* from Hyperion’s core!", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚙️ Usage: ,forge <unit> <count>")
        unit = parts[1]
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Count must be a number.")
        army = json.loads(p["Army"])
        cost_ore = {"scout": 10, "tank": 20, "drone": 30}
        cost_credits = {"scout": 5, "tank": 10, "drone": 15}
        if unit not in army:
            return await update.message.reply_text("⚠ Invalid unit type.")
        total_ore = cost_ore[unit] * count
        total_credits = cost_credits[unit] * count
        if p["Ore"] < total_ore or p["Credits"] < total_credits:
            return await update.message.reply_text("⚠ Insufficient resources.")
        p["Ore"] -= total_ore
        p["Credits"] -= total_credits
        army[unit] += count
        p["Army"] = json.dumps(army)
        update_player(p)
        return await update.message.reply_text(f"⚙️ Forged *{count} {unit}(s)* into your mighty army.", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",blackmarket"):
        if not p.get("BlackMarketUnlocked", False):
            return await update.message.reply_text("🔒 You must unlock access! Use ,unlockbm first.")
        bm_items = "\n".join([f"- {k}: {v['desc']}" for k, v in blackmarket.items()])
        return await update.message.reply_text(f"🛒 *Black Market Items:*\n{bm_items}", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",unlockbm"):
        if p.get("BlackMarketUnlocked", False):
            return await update.message.reply_text("✅ Already unlocked.")
        if p["Credits"] < 500:
            return await update.message.reply_text("❌ Need 500 credits to unlock Black Market.")
        p["Credits"] -= 500
        p["BlackMarketUnlocked"] = True
        save_player(p)
        return await update.message.reply_text("🎉 Black Market access unlocked!")

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buy <item>")
        item = parts[1]
        if item not in blackmarket:
            return await update.message.reply_text("❌ Item does not exist.")
        cost = blackmarket[item]["cost"]
        if p["Credits"] < cost:
            return await update.message.reply_text("❌ Not enough credits.")
        items_owned = json.loads(p["Items"])
        items_owned[item] = items_owned.get(item, 0) + 1
        p["Credits"] -= cost
        p["Items"] = json.dumps(items_owned)
        save_player(p)
        return await update.message.reply_text(f"✅ Bought {item}!")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
        item = parts[1]
        items_owned = json.loads(p["Items"])
        if items_owned.get(item, 0) <= 0:
            return await update.message.reply_text("❌ You don't own this item.")
        if item in perishables:
            items_owned[item] -= 1
            if items_owned[item] == 0:
                del items_owned[item]
            p["Items"] = json.dumps(items_owned)
            save_player(p)
        return await update.message.reply_text(f"✅ Used {item}!")

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,attack <playername>")
        target_name = parts[1]
        target_id, target = find_by_name(target_name)
        if not target:
            return await update.message.reply_text("❌ Target not found.")
        if p["Energy"] < 20:
            return await update.message.reply_text("⚡ Not enough energy.")
        p["Energy"] -= 20
        if p["Army"]["scout"] > target["Army"]["scout"]:
            return await update.message.reply_text(f"⚔️ Victory over {target_name}!")
        else:
            return await update.message.reply_text(f"💥 Defeated by {target_name}...")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "🛠 *SkyHustle Commands:*\n"
            "`,start` - Begin your journey\n"
            "`,name <alias>` - Set your callsign\n"
            "`,status` - View your stats\n"
            "`,daily` - Claim daily reward\n"
            "`,mine ore <count>` - Mine Hyperion ore\n"
            "`,forge <unit> <count>` - Build army units\n"
            "`,blackmarket` - View Black Market\n"
            "`,unlockbm` - Unlock Black Market access\n"
            "`,buy <item>` - Purchase Black Market item\n"
            "`,use <item>` - Use an owned item\n"
            "`,attack <playername>` - Attack another player\n"
            "`,help` - Show this help list",
            parse_mode=ParseMode.MARKDOWN
        )

    await update.message.reply_text("❓ Unknown command. Type ,help for available actions.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
