# handlers/chaos.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.chaos_storms_manager import STORMS, can_trigger, trigger_storm
from utils.format_utils import section_header

async def chaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos – show the Chaos Storms catalog and trigger one if available.
    """
    # Build the catalog header
    lines = [
        section_header("🎲 Chaos Storms Catalog", pad_char="=", pad_count=3),
        ""
    ]

    # List all storms (name + teaser)
    for s in STORMS:
        teaser = s["story"].splitlines()[0]
        lines.append(f"{s['emoji']} *{s['name']}* — {teaser}")
    lines.append("")

    # Trigger a storm if it's off cooldown
    if can_trigger():
        storm = trigger_storm()
        lines.append(section_header("🌪️ Chaos Storm Struck!", pad_char="-", pad_count=3))
        lines.append(f"{storm['emoji']} *{storm['name']}*")
        for paragraph in storm["story"].splitlines():
            lines.append(paragraph)
        lines.append("")
        lines.append("⚡ Brace yourself for unpredictable effects!")
    else:
        lines.append("⏳ A Chaos Storm recently struck.")
        lines.append("Next one will occur in a few days.")
    
    text = "\n".join(lines)

    # Inline Refresh button
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh Catalog", callback_data="chaos")
    )

    if update.message:
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )

async def chaos_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "chaos":
        return await chaos(update, context)

handler = CommandHandler("chaos", chaos)
callback_handler = CallbackQueryHandler(chaos_button, pattern="^chaos$")
