# handlers/challenges.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.challenge_manager import (
    load_challenges,
    award_challenges,
    get_player_challenge,
)
from utils.format_utils import section_header, format_bar

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    # 1) Announce completed dailies
    awards = award_challenges(uid, 'daily')
    for ch in awards:
        header = section_header("🎉 Daily Challenge Complete!", pad_char="=", pad_count=3)
        text = (
            f"{header}\n\n"
            f"*{ch.description}*\n"
            f"Rewards: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # 2) List current dailies with progress bars
    challenges = load_challenges('daily')
    lines = [section_header("🗓️ Daily Challenges", pad_char="=", pad_count=3), ""]
    for ch in challenges:
        idx, prow = get_player_challenge(uid, ch.id)
        prog = int(prow[4] or 0) if prow else 0
        done = prow and prow[3]
        bar = format_bar(ch.value, ch.value) if done else format_bar(prog, ch.value)
        status = "✅ " if done else ""
        lines.append(
            f"{bar} {status}{ch.description}\n"
            f"   (Reward: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡)"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    # 1) Announce completed weeklies
    awards = award_challenges(uid, 'weekly')
    for ch in awards:
        header = section_header("🎉 Weekly Challenge Complete!", pad_char="=", pad_count=3)
        text = (
            f"{header}\n\n"
            f"*{ch.description}*\n"
            f"Rewards: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # 2) List current weeklies with progress bars
    challenges = load_challenges('weekly')
    lines = [section_header("📅 Weekly Challenges", pad_char="=", pad_count=3), ""]
    for ch in challenges:
        idx, prow = get_player_challenge(uid, ch.id)
        prog = int(prow[4] or 0) if prow else 0
        done = prow and prow[3]
        bar = format_bar(ch.value, ch.value) if done else format_bar(prog, ch.value)
        status = "✅ " if done else ""
        lines.append(
            f"{bar} {status}{ch.description}\n"
            f"   (Reward: +{ch.reward_credits}💳 +{ch.reward_minerals}⛏️ +{ch.reward_energy}⚡)"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler_daily  = CommandHandler('daily', daily)
handler_weekly = CommandHandler('weekly', weekly)
