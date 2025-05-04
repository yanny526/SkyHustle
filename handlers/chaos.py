from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from modules.chaos_storms_manager import get_random_storm, apply_storm

async def chaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos – trigger a random Chaos Storm for all commanders.
    Selects one event, applies its effects to every player,
    and broadcasts the vivid storm story.
    """
    storm = get_random_storm()
    apply_storm(storm)

    title = f"{storm['emoji']} *{storm['name']}*"
    text = (
        f"{title}\n\n"
        f"{storm['story']}\n\n"
        "⚠️ These storms strike randomly once a week, so brace yourself for the next one!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('chaos', chaos)
