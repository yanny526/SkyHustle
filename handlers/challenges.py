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
