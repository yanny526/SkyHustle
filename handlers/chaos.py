from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.chaos_storms_manager import trigger_storm

async def chaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos – trigger a random Chaos Storm for all commanders,
    once per week.
    """
    storm = trigger_storm()
    if not storm:
        await update.message.reply_text(
            "⚠️ A Chaos Storm has recently struck. "
            "Next storm will be available in a few days!"
        )
        return

    title = f"{storm['emoji']} *{storm['name']}*"
    text = (
        f"{title}\n\n"
        f"{storm['story']}\n\n"
        "⚠️ These storms strike randomly once a week—brace yourself!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler("chaos", chaos)
