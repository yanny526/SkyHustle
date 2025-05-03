from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades
from modules.achievement_manager import check_and_award_achievements

def game_command(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)

        # Safe message object (for /commands or button clicks)
        message = update.message or (update.callback_query and update.callback_query.message)
        if not message:
            return

        # 1) Tick resources
        added = tick_resources(uid)
        if added['minerals'] or added['energy']:
            await message.reply_text(
                f"🌱 +{added['minerals']} Minerals, +{added['energy']} Energy"
            )

        # 2) Complete upgrades
        done = complete_upgrades(uid)
        if done:
            msgs = "\n".join(
                f"✅ {btype} upgrade complete! Now Lvl {lvl}."
                for btype, lvl in done
            )
            await message.reply_text(msgs)

        # 3) Run the original command
        result = await func(update, context)

        # 4) Check for newly unlocked achievements
        awards = check_and_award_achievements(uid)
        for ach in awards:
            await message.reply_text(
                f"🏅 *Achievement unlocked!* {ach.description}\n"
                f"Rewards: +{ach.reward_credits}💳 +{ach.reward_minerals}⛏️ +{ach.reward_energy}⚡",
                parse_mode=ContextTypes.MARKDOWN
            )

        return result

    return wrapper
