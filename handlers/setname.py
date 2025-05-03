# handlers/setname.py

import time
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname <name> - Set your unique commander name and unlock your first reward.
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
            f"⚠️ The name *{name}* is already taken.\nTry a unique variation like `{name}_X`.",
            parse_mode=ParseMode.MARKDOWN
        )

    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        if row[0] == uid:
            is_first_time = row[1].strip() in ["", "leader", "commander"]
            row[1] = name  # Update the commander name

            # 🏆 First-time reward logic
            if is_first_time and (len(row) < 8 or row[7].strip() == ""):
                while len(row) < 8:
                    row.append("")
                row[5] = str(int(row[5]) + 500)  # +500 energy
                row[7] = "step1"
                update_row("Players", idx, row)

                # Send reward + onboarding task
                await update.message.reply_text(
                    f"✅ Your new commander name is *{name}*!\n"
                    "🎁 You’ve earned *+500 ⚡ Energy* for completing your first task!",
                    parse_mode=ParseMode.MARKDOWN
                )

                intro = (
                    "🌍 *The world is in ruins.*\n"
                    "You are the last hope of your region.\n"
                    "Command your base, rebuild power, and rise to dominate.\n\n"
                    "🧰 You’ve received a starter pack:\n"
                    "💳 1000 Credits\n⛏️ 1000 Minerals\n⚡ 1000 Energy\n\n"
                    "📋 *Your first task:*\n"
                    "`/build powerplant` – Start generating energy.\n\n"
                    "After that, use `/status` to check your base.\n"
                    "_You can always open /menu for commands._"
                )

                reply_markup = ReplyKeyboardMarkup(
                    [[KeyboardButton("/build powerplant")], [KeyboardButton("/status")]],
                    resize_keyboard=True
                )

                return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

            # Just a name update, no reward
            update_row("Players", idx, row)
            return await update.message.reply_text(
                f"✅ Commander name updated to *{name}*!\n"
                "Use /menu to begin your conquest.",
                parse_mode=ParseMode.MARKDOWN
            )

    await update.message.reply_text(
        "❗ You are not registered yet. Use /start first.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("setname", setname)
