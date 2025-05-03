# handlers/leaderboard.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from utils.decorators import game_command

@game_command
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard - show top commanders by power (tick & upgrades via decorator).
    """
    players = get_rows('Players')[1:]
    buildings = get_rows('Buildings')[1:]
    army = get_rows('Army')[1:]

    # Sum building levels
    build_power = {}
    for uid, _, lvl_str, *_ in buildings:
        build_power[uid] = build_power.get(uid, 0) + int(lvl_str)

    # Sum army power
    army_power = {}
    for uid, unit, count_str in army:
        p = int(count_str) * {'infantry': 10, 'tanks': 50, 'artillery': 100}[unit]
        army_power[uid] = army_power.get(uid, 0) + p

    # Compile scores
    scores = []
    for uid, commander_name, _, *__ in players:
        name = commander_name or "Unknown"
        total = build_power.get(uid, 0) + army_power.get(uid, 0)
        scores.append((name, total))
    scores.sort(key=lambda x: x[1], reverse=True)

    lines = ["🏆 *Leaderboard* 🏆\n"]
    for idx, (name, power) in enumerate(scores[:10], start=1):
        lines.append(f"{idx}. *{name}* — {power} Power")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('leaderboard', leaderboard)
