# handlers/leaderboard.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard - show top 10 commanders by Total Power.
    Total Power = sum(building levels) + sum(unit strength)
    """
    # Fetch data
    players = get_rows('Players')[1:]     # skip header
    buildings = get_rows('Buildings')[1:]
    army = get_rows('Army')[1:]

    # Sum building levels per user
    build_power = {}
    for uid, btype, lvl_str, *rest in buildings:
        lvl = int(lvl_str)
        build_power[uid] = build_power.get(uid, 0) + lvl

    # Sum army power per user
    army_power = {}
    for uid, unit, count_str in army:
        count = int(count_str)
        if unit.lower() == 'infantry':
            p = count * 10
        elif unit.lower() == 'tanks':
            p = count * 50
        elif unit.lower() == 'artillery':
            p = count * 100
        else:
            p = 0
        army_power[uid] = army_power.get(uid, 0) + p

    # Build score list
    scores = []
    for uid, commander_name, tg_username, *_ in players:
        name = commander_name or tg_username or "Unknown"
        total = build_power.get(uid, 0) + army_power.get(uid, 0)
        scores.append((name, total))

    # Sort and take top 10
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:10]

    # Compose output
    lines = ["🏆 *Leaderboard* 🏆\n"]
    for idx, (name, power) in enumerate(top, start=1):
        lines.append(f"{idx}. *{name}* — {power} Power")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('leaderboard', leaderboard)
