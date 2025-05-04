# handlers/chaos.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.chaos_storms_manager import STORMS, can_trigger, trigger_storm

async def chaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos – show all Chaos Storms and trigger one if available.
    """
    # Build catalog of all storms
    catalog = [
        f"• {s['emoji']} *{s['name']}* — {s['story'].splitlines()[0]}"
        for s in STORMS
    ]
    text = "🎲 *Chaos Storms Catalog:*\n" + "\n".join(catalog)

    # Trigger if cooldown passed
    if can_trigger():
        storm = trigger_storm()
        trigger_text = (
            f"\n\n🌪️ *Chaos Storm Struck!* {storm['emoji']} *{storm['name']}*\n"
            f"{storm['story']}\n\n"
            "⚡ Brace yourself for unpredictable effects!"
        )
        text += trigger_text
    else:
        text += "\n\n⏳ A Chaos Storm recently struck. Next one available in a few days!"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler("chaos", chaos)
