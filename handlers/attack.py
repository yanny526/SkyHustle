# handlers/attack.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.combat import Combat
from utils.format import section_header

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    uid = str(update.effective_user.id)
    
    if not args:
        await update.message.reply_text(
            "Use the /scan command to get suggested targets!",
            parse_mode="Markdown"
        )
        return

    target_id = args[0]

    # Initialize combat
    combat = Combat(uid, target_id)
    report, outcome = combat.resolve_combat()

    await update.message.reply_text(
        report,
        parse_mode="Markdown"
    )
