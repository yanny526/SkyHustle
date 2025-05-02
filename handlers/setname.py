# handlers/setname.py

import time
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname <name> - set your unique commander name (letters, numbers, underscores only).
    """
    user = update.effective_user
    args = context.args

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/setname <YourName>`\n"
            "Example: `/setname IronLegion`",
            parse_mode="Markdown"
        )

    name = args[0].strip()
    if not name.replace('_', '').isalnum():
        return await update.message.reply_text(
            "❌ Invalid name. Use only letters, numbers, or underscores (no spaces)."
        )

    rows = get_rows('Players')
    taken = {row[1] for row in rows[1:] if len(row) > 1 and row[1]}
    if name in taken:
        return await update.message.reply_text(
            f"⚠️ Commander name *{name}* is already taken. Choose another.",
            parse_mode="Markdown"
        )

    for idx, row in enumerate(rows):
        if idx == 0: continue
        if str(row[0]) == str(user.id):
            row[1] = name
            update_row('Players', idx, row)
            return await update.message.reply_text(
                f"✅ Commander name set to *{name}*!\n"
                "Use /menu to begin your conquest.",
                parse_mode="Markdown"
            )

    await update.message.reply_text(
        "❗ You need to run `/start` first to register.",
        parse_mode="Markdown"
    )

handler = CommandHandler('setname', setname)
