from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import date, datetime, timedelta
from data import players
from utils import find_by_name

def make_player():
    return {
        "name": "", "zone": None, "shield": None,
        "ore": 0, "energy": 100, "credits": 0, "last_mine": None,
        "spy_level": 0, "refinery_level": 0, "defense_level": 0, "lab_level": 0,
        "army": {"scout": 0, "tank": 0, "drone": 0},
        "research": {"speed": 0, "armor": 0},
        "wins": 0, "losses": 0, "rank": 0,
        "daily_streak": 0, "last_daily": None, "daily_done": False,
        "faction": None, "achievements": set()
    }

def get_player(cid):
    if cid not in players:
        players[cid] = make_player()
    return players[cid]

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

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
        ocid, _ = find_by_name(alias, players)
        if ocid and ocid != cid:
            return await update.message.reply_text("❌ Alias taken.")
        p["name"] = alias
        return await update.message.reply_text(f"🚩 Callsign set to {alias}")

    if text.startswith(",status"):
        shield = p["shield"].strftime("%H:%M:%S") if p["shield"] and now < p["shield"] else "None"
        msg = (
            f"📊 {p['name'] or 'Commander'} Status:
"
            f"🪨 Ore: {p['ore']}  ⚡ Energy: {p['energy']}  💳 Credits: {p['credits']}
"
            f"🏭 Blds: Spy{p['spy_level']} Ref{p['refinery_level']} Def{p['defense_level']} Lab{p['lab_level']}
"
            f"🎖 Rank: {p['rank']}  🏅 Streak: {p['daily_streak']}d
"
            f"🤖 Army: {p['army']}
"
            f"🛡 Shield: {shield}
"
            f"📍 Zone: {p['zone'] or 'None'}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    await update.message.reply_text("❓ Unknown command. Type ,help.")
