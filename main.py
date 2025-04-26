# SkyHustle - Full Beautified Main

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, date, timedelta
import os
import json
from sheet import get_sheet

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

# Google Sheet Connection
players_sheet = get_sheet().worksheet("SkyHustle")

def make_player(cid):
    return {
        "ChatID": cid, "Name": "", "Ore": 0, "Energy": 100, "Credits": 100,
        "Army": json.dumps({"scout": 0, "tank": 0, "drone": 0}),
        "Zone": "", "ShieldUntil": "", "DailyStreak": 0, "LastDaily": "",
        "BlackMarketUnlocked": False, "Items": json.dumps({})
    }

def get_player(cid):
    records = players_sheet.get_all_records()
    for idx, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = idx + 2
            return row
    # New player
    new_p = make_player(cid)
    players_sheet.append_row(list(new_p.values()))
    new_p["_row"] = len(records) + 2
    return new_p

def update_player(p):
    players_sheet.update(
        f"A{p['_row']}:L{p['_row']}",
        [[
            p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"], p["Army"],
            p["Zone"], p["ShieldUntil"], p["DailyStreak"], p["LastDaily"],
            p["BlackMarketUnlocked"], p["Items"]
        ]]
    )

def save_player(p):
    update_player(p)

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        intro = (
            "🌌 **Welcome, Commander!**\n\n"
            "The year is *3147*. Humanity lies scattered among shattered worlds.\n"
            "You are chosen to rebuild, conquer, and forge your destiny. 🌟\n\n"
            "⚙️ Set your callsign: `,name <alias>`\n"
            "📊 View stats: `,status`\n"
            "⛏ Begin mining: `,mine ore 1`\n"
            "🎯 Claim daily rewards: `,daily`\n\n"
            "⚡ **May the stars favor your rise!**"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",help"):
        help_text = (
            "🆘 **SkyHustle Commands:**\n\n"
            "🚀 `,start` - Begin your journey\n"
            "🎖 `,name <alias>` - Set your Commander name\n"
            "📊 `,status` - View your resources and army\n"
            "🎁 `,daily` - Claim daily energy and credits\n"
            "⛏ `,mine ore <count>` - Mine ore using energy\n"
            "🛠 `,forge <unit> <count>` - Build war units\n"
            "🏰 `,claim <zone>` - Seize control of a zone\n"
            "🛒 `,store` - View regular store\n"
            "🕵️ `,blackmarket` - Enter the secret Black Market\n"
            "🛡 `,use <item>` - Use special items\n"
            "🌎 `,map` - View world zone control\n"
            "🎯 `,missions` - View missions (WIP)"
        )
        return await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠️ Usage: `,name <alias>`", parse_mode=ParseMode.MARKDOWN)
        p["Name"] = alias
        save_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to **{alias}**", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items_owned = ", ".join([f"{k}x{v}" for k, v in json.loads(p["Items"]).items()]) or "None"
        shield = p["ShieldUntil"] or "None"
        msg = (
            f"📜 **Commander {p['Name'] or 'Unknown'}'s Status:**\n\n"
            f"🪨 Ore: `{p['Ore']}`   ⚡ Energy: `{p['Energy']}`   💳 Credits: `{p['Credits']}`\n"
            f"🤖 Army: `{army}`\n"
            f"📦 Items: `{items_owned}`\n"
            f"🛡 Shield Until: `{shield}`\n"
            f"🌎 Zone: `{p['Zone'] or 'None'}`"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 You already claimed today's reward!")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        streak = int(p["DailyStreak"])
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 25
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        save_player(p)
        return await update.message.reply_text(f"🎁 +50 Credits, +25 Energy! 🔥 Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠️ Usage: `,mine ore <count>`", parse_mode=ParseMode.MARKDOWN)
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠️ Mining count must be a number.", parse_mode=ParseMode.MARKDOWN)
        if int(p["Energy"]) < count * 5:
            return await update.message.reply_text("⚡ Not enough energy!")
        ore_gain = 20 * count
        p["Ore"] = int(p["Ore"]) + ore_gain
        p["Energy"] = int(p["Energy"]) - count * 5
        save_player(p)
        return await update.message.reply_text(f"⛏ You mined {ore_gain} Ore! (+{10*count} bonus Credits)", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",map"):
        records = players_sheet.get_all_records()
        control = {}
        for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
            owner = next((r["Name"] for r in records if r["Zone"] == z), "Unclaimed")
            control[z] = owner
        out = "🗺 **World Zone Control:**\n\n"
        for zone, owner in control.items():
            out += f"🏰 {zone}: **{owner}**\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",store"):
        store = (
            "🛒 **Regular Store:**\n\n"
            "🔹 `,forge scout 1` - Cheap explorer (10 Ore + 5 Credits)\n"
            "🔹 `,forge drone 1` - Versatile unit (15 Ore + 10 Credits)\n"
            "🔹 `,forge tank 1` - Heavy hitter (30 Ore + 20 Credits)"
        )
        return await update.message.reply_text(store, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",blackmarket"):
        if str(p["BlackMarketUnlocked"]).lower() != "true":
            return await update.message.reply_text(
                "🕵️ Unlock Black Market for *500 credits*: `,unlockbm`\n\n"
                "Once unlocked, you access rare and devastating items!",
                parse_mode=ParseMode.MARKDOWN
            )
        blackmarket = (
            "🛒 **Black Market Deals:**\n\n"
            "🔹 `,buy infinityscout1` - Ultra Scout (1-use)\n"
            "🔹 `,buy reviveall` - Revive all army units\n"
            "🔹 `,buy hazmat` - Enter Radiation Zones"
        )
        return await update.message.reply_text(blackmarket, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",unlockbm"):
        if int(p["Credits"]) < 500:
            return await update.message.reply_text("❌ You need 500 credits to unlock Black Market.")
        p["Credits"] = int(p["Credits"]) - 500
        p["BlackMarketUnlocked"] = True
        save_player(p)
        return await update.message.reply_text("✅ Black Market unlocked!")

    await update.message.reply_text("❓ Unknown command. Type `,help` for the command list.", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
