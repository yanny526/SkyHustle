# handlers/leaderboard.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row
from utils.decorators import game_command
from modules.unit_manager import UNITS  # dynamic unit power lookup

@game_command
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard - show top commanders by power and reward Top 3 placement.
    """
    # Load players sheet (including header)
    players_sheet = get_rows('Players')
    header = players_sheet[0]
    data = players_sheet[1:]

    # Sum building power
    buildings = get_rows('Buildings')[1:]
    build_power = {}
    for row in buildings:
        try:
            uid, _, lvl_str, *_ = row
            build_power[uid] = build_power.get(uid, 0) + int(lvl_str)
        except:
            continue

    # Sum army power
    army = get_rows('Army')[1:]
    army_power = {}
    for row in army:
        try:
            uid, unit, count_str = row
            _, _, _, power, _ = UNITS[unit]
            army_power[uid] = army_power.get(uid, 0) + int(count_str) * power
        except:
            continue

    # Compile scores with UID
    scores = []  # list of (uid, name, total_power)
    for row in data:
        try:
            uid = row[0]
            name = row[1] or "Unknown"
            total = build_power.get(uid, 0) + army_power.get(uid, 0)
            scores.append((uid, name, total))
        except:
            continue
    
    # Sort descending
    scores.sort(key=lambda x: x[2], reverse=True)

    # Reward Top 3 who haven't received badge
    badge_idx = None
    for i, col in enumerate(header):
        if col.lower() == 'badge':
            badge_idx = i
            break
    # default reward values
    credit_reward = 2000
    mineral_reward = 1000
    badge_text = '🏅 Top 3 Commander'

    # Iterate Top 3
    for position, (uid, name, _) in enumerate(scores[:3], start=1):
        # find row index in sheet
        for ridx, prow in enumerate(players_sheet[1:], start=1):
            if prow[0] == uid:
                # ensure prow list matches header length
                while len(prow) < len(header): prow.append('')
                # check badge cell
                if badge_idx is not None and prow[badge_idx] != badge_text:
                    # grant rewards
                    prow[3] = str(int(prow[3]) + credit_reward)
                    prow[4] = str(int(prow[4]) + mineral_reward)
                    prow[badge_idx] = badge_text
                    update_row('Players', ridx, prow)
                    # send congrats
                    reward_msg = (
                        f"🎉 Congratulations, Commander *{name}*!\n"
                        f"You’ve achieved *Top {position}* on the leaderboard!\n"
                        f"As a reward: +{credit_reward}💳 Credits and +{mineral_reward}⛏️ Minerals!"
                    )
                    # DM or chat message
                    if update.message:
                        await update.message.reply_text(reward_msg, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await context.bot.send_message(update.effective_chat.id, reward_msg, parse_mode=ParseMode.MARKDOWN)
                break

    # Build leaderboard text
    lines = ["🏆 *Leaderboard* 🏆\n"]
    for idx, (_, name, power) in enumerate(scores[:10], start=1):
        lines.append(f"{idx}. *{name}* — {power} Power")
    text = "\n".join(lines)

    # Respond appropriately
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('leaderboard', leaderboard)
