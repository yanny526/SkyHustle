# handlers/chaos.py

from telegram import Update, ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.chaos_storms_manager import EVENTS

async def chaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos – preview all Random Chaos Storms.
    """
    lines = ["🌪️ *Random Chaos Storms* 🌪️\n"]
    for ev in EVENTS:
        lines.append(f"{ev['emoji']} *{ev['title']}*")
        lines.append(f"_{ev['story']}_\n")
    lines.append("_One of these storms will strike randomly once a week!_")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler("chaos", chaos)
