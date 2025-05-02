
# utils/decorators.py

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from modules.resource_manager import tick_resources
from modules.upgrade_manager import complete_upgrades

def game_command(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)

        # 1) Tick resources
        added = tick_resources(uid)
        if added['minerals'] or added['energy']:
            await update.message.reply_text(
                f"🌱 +{added['minerals']} Minerals, +{added['energy']} Energy"
            )

        # 2) Complete upgrades
        done = complete_upgrades(uid)
        if done:
            msgs = "\n".join(
                f"✅ {btype} upgrade complete! Now Lvl {lvl}."
                for btype, lvl in done
            )
            await update.message.reply_text(msgs)

        # 3) Run the original command
        return await func(update, context)

    return wrapper
