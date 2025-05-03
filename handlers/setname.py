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
    header = rows[0]
    # collect taken names
    taken = {r[1].strip().lower() for r in rows[1:] if len(r) > 1 and r[1]}

    if name.lower() in taken:
        return await update.message.reply_text(
            f"⚠️ The name *{name}* is already taken. Try `{name}_X`.",
            parse_mode=ParseMode.MARKDOWN
        )

    # find and update player row
    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        if row[0] == uid:
            # ensure row has same length as header
            while len(row) < len(header):
                row.append("")

            original = row[1].strip()
            first_time = original == ""
            row[1] = name  # set commander name

            # first-time reward logic
            if first_time and row[7] != "step1":
                # +500 energy reward
                row[5] = str(int(row[5]) + 500)
                row[7] = "step1"
                update_row("Players", idx, row)

                # confirm name and reward
                await update.message.reply_text(
                    f"✅ Your commander name is *{name}*!\n"
                    "🎁 You’ve earned +500 ⚡ Energy for Task 1.",
                    parse_mode=ParseMode.MARKDOWN
                )

                # next quest text
                text2 = (
                    "🛡️ *You are the last hope of your region.*\n"
                    "Command your base, rebuild power, and rise to dominate.\n\n"
                    "🧾 *Your second task:*\n"
                    "`/build powerplant` – Start generating energy.\n\n"
                    "🎁 *On completion you’ll earn:* +100 ⛏️ Minerals\n"
                    
                )
                markup2 = ReplyKeyboardMarkup(
                    [[KeyboardButton("/build powerplant")], [KeyboardButton("/status")]],
                    resize_keyboard=True
                )
                return await update.message.reply_text(
                    text2,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=markup2
                )

            # not first-time or already rewarded
            update_row("Players", idx, row)
            return await update.message.reply_text(
                f"✅ Commander name updated to *{name}*!\n"
                "Use /menu to continue your conquest.",
                parse_mode=ParseMode.MARKDOWN
            )

    # user not registered
    await update.message.reply_text(
        "❗ You need to run `/start` first to register.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("setname", setname)
