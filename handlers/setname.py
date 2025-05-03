# handlers/setname.py

import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname <name> - Set your unique commander name.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/setname <YourName>`\n"
            "Example: `/setname IronLegion`",
            parse_mode=ParseMode.MARKDOWN
        )

    name = args[0].strip()
    if not name.replace("_", "").isalnum():
        return await update.message.reply_text(
            "🚫 Invalid name. Only letters, numbers, and underscores are allowed (no spaces or symbols)."
        )

    rows = get_rows("Players")
    name_taken = any(row[1].strip().lower() == name.lower() for row in rows[1:] if len(row) > 1)

    if name_taken:
        return await update.message.reply_text(
            f"⚠️ The name *{name}* is already taken.\nTry a unique variation like `{name}X` or `{name}_77`.",
            parse_mode=ParseMode.MARKDOWN
        )

    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        if row[0] == uid:
            row[1] = name
            update_row("Players", idx, row)
            return await update.message.reply_text(
                f"✅ Your new commander name is *{name}*!\n"
                "Now use /build or /status to grow your empire.",
                parse_mode=ParseMode.MARKDOWN
            )

    await update.message.reply_text(
        "❗ You are not registered yet. Use /start first.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("setname", setname)
