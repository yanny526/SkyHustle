# modules/challenge_manager.py

from sheets_service import get_rows, append_row, update_row
from datetime import date

class Challenge:
    def __init__(self, cid, ctype, description, key, value, reward_credits, reward_minerals, reward_energy):
        self.id = cid
        self.type = ctype
        self.description = description
        self.key = key
        self.value = int(value)
        self.reward_credits = int(reward_credits)
        self.reward_minerals = int(reward_minerals)
        self.reward_energy = int(reward_energy)


def load_challenges(ch_type: str):
    """Load active challenges of given type ('daily' or 'weekly')."""
    rows = get_rows("Challenges")
    header, data = rows[0], rows[1:]
    challenges = []
    idx = {col: i for i, col in enumerate(header)}
    for row in data:
        if row[idx['type']].lower() != ch_type:
            continue
        if row[idx['active']].lower() != 'true':
            continue
        challenges.append(Challenge(
            cid=row[idx['challenge_id']],
            ctype=row[idx['type']],
            description=row[idx['description']],
            key=row[idx['requirement_key']],
            value=row[idx['requirement_value']],
            reward_credits=row[idx['reward_credits']],
            reward_minerals=row[idx['reward_minerals']],
            reward_energy=row[idx['reward_energy']],
        ))
    return challenges


def get_player_challenge(uid: str, cid: str):
    """Return (row_index, row) for a player's challenge entry today."""
    rows = get_rows("PlayerChallenges")
    header, data = rows[0], rows[1:]
    today = date.today().isoformat()
    for i, row in enumerate(data, start=1):
        if row[0] == uid and row[1] == cid and row[2] == today:
            return i, row
    return None, None


def update_player_progress(uid: str, ch: Challenge, increment: int = 1):
    """Increment progress and mark complete if threshold reached."""
    pc_idx, prow = get_player_challenge(uid, ch.id)
    if prow:
        prog = int(prow[4] or 0) + increment
        prow[4] = str(prog)
        if prog >= ch.value and not prow[3]:
            prow[3] = date.today().isoformat()  # date_completed
        update_row("PlayerChallenges", pc_idx, prow)
    else:
        completed = date.today().isoformat() if increment >= ch.value else ""
        append_row("PlayerChallenges", [uid, ch.id, today, completed, str(increment)])


def award_challenges(uid: str, ch_type: str):
    """Grant rewards for any completed but not yet awarded challenges."""
    challenges = load_challenges(ch_type)
    for ch in challenges:
        pc_idx, prow = get_player_challenge(uid, ch.id)
        if prow and prow[3] and prow[5] != 'awarded':  # assuming column 5 is a flag
            # grant resources
            players = get_rows("Players")
            ph, pd = players[0], players[1:]
            pidx = [r[0] for r in pd].index(uid) + 1
            row = players[pidx]
            row[3] = str(int(row[3]) + ch.reward_credits)
            row[4] = str(int(row[4]) + ch.reward_minerals)
            row[5] = str(int(row[5]) + ch.reward_energy)
            update_row("Players", pidx, row)
            # mark awarded
            prow[5] = 'awarded'
            update_row("PlayerChallenges", pc_idx, prow)


# handlers/challenges.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.challenge_manager import load_challenges, award_challenges, update_player_progress

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    # Check and award any completed dailies
    award_challenges(uid, 'daily')
    # List current daily challenges
    challenges = load_challenges('daily')
    lines = ['🗓️ *Daily Challenges*', '']
    for ch in challenges:
        idx, prow = get_player_challenge(uid, ch.id)
        prog = int(prow[4] or 0) if prow else 0
        status = '✅' if prow and prow[3] else f'{prog}/{ch.value}'
        lines.append(f'{status} {ch.description} (Reward: {ch.reward_credits}💳 {ch.reward_minerals}⛏️ {ch.reward_energy}⚡)')
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN)

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    award_challenges(uid, 'weekly')
    challenges = load_challenges('weekly')
    lines = ['📅 *Weekly Challenges*', '']
    for ch in challenges:
        idx, prow = get_player_challenge(uid, ch.id)
        prog = int(prow[4] or 0) if prow else 0
        status = '✅' if prow and prow[3] else f'{prog}/{ch.value}'
        lines.append(f'{status} {ch.description} (Reward: {ch.reward_credits}💳 {ch.reward_minerals}⛏️ {ch.reward_energy}⚡)')
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN)

# Register handlers in your main.py:
# app.add_handler(CommandHandler('daily', daily))
# app.add_handler(CommandHandler('weekly', weekly))

