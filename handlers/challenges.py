from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.challenge_manager import (
    load_challenges,
    award_challenges,
    update_player_progress,
    get_player_challenge,
)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    # 1) Award any newly completed dailies and send messages
    awards = award_challenges(uid, 'daily')
    for ch in awards:
        await update.message.reply_text(
            f"🎉 *Daily Complete!* {ch.description}\n"
            f"Rewards: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡",
            parse_mode=ParseMode.MARKDOWN
        )

    # 2) Show current progress
    challenges = load_challenges('daily')
    lines = ['🗓️ *Daily Challenges*', '']
    for ch in challenges:
        idx, prow = get_player_challenge(uid, ch.id)
        prog = int(prow[4] or 0) if prow else 0
        done = prow and prow[3]
        status = '✅' if done else f'{prog}/{ch.value}'
        lines.append(
            f'{status} {ch.description} '
            f'(Reward: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡)'
        )
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN)

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    # 1) Award any newly completed weeklies and send messages
    awards = award_challenges(uid, 'weekly')
    for ch in awards:
        await update.message.reply_text(
            f"🎉 *Weekly Complete!* {ch.description}\n"
            f"Rewards: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡",
            parse_mode=ParseMode.MARKDOWN
        )

    # 2) Show current progress
    challenges = load_challenges('weekly')
    lines = ['📅 *Weekly Challenges*', '']
    for ch in challenges:
        idx, prow = get_player_challenge(uid, ch.id)
        prog = int(prow[4] or 0) if prow else 0
        done = prow and prow[3]
        status = '✅' if done else f'{prog}/{ch.value}'
        lines.append(
            f'{status} {ch.description} '
            f'(Reward: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡)'
        )
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN)

handler_daily = CommandHandler('daily', daily)
handler_weekly = CommandHandler('weekly', weekly)
