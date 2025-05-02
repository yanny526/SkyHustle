# handlers/leaderboard.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard - show top 10 commanders by Total Power,
    after ticking resources and completing upgrades for you.
    """
    user = update.effective_user
    uid = str(user.id)

    # 1) Tick resources & complete upgrades for current user
    tick_resources(uid)
    done = complete_upgrades(uid)
    if done:
        msgs = "\n".join(
            f"✅ {btype} upgrade complete! Now Lvl {lvl}."
            for btype, lvl in done
        )
        await update.message.reply_text(msgs)

    # 2) Gather all data
    players = get_rows('Players')[1:]
    buildings = get_rows('Buildings')[1:]
    army = get_rows('Army')[1:]

    # 3) Compute building power
    build_power = {}
    for p_uid, btype, lvl_str, *_ in buildings:
        build_power[p_uid] = build_power.get(p_uid, 0) + int(lvl_str)

    # 4) Compute army power
    army_power = {}
    for p_uid, unit, count_str in army:
        p = int(count_str) * ({
            'infantry': 10,
            'tanks': 50,
            'artillery': 100
        }[unit.lower()])
        army_power[p_uid] = army_power.get(p_uid, 0) + p

    # 5) Build and sort score list
    scores = []
    for p_uid, commander_name, tg_username, *rest in players:
        name = commander_name or tg_username or "Unknown"
        total = build_power.get(p_uid, 0) + army_power.get(p_uid, 0)
        scores.append((name, total))
    scores.sort(key=lambda x: x[1], reverse=True)

    # 6) Take top 10 and reply
    lines = ["🏆 *Leaderboard* 🏆\n"]
    for idx, (name, power) in enumerate(scores[:10], start=1):
        lines.append(f"{idx}. *{name}* — {power} Power")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('leaderboard', leaderboard)
