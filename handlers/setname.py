# handlers/setname.py

import time
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname <name> - set your commander name, grant first reward,
    then deliver the second quest.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args

    if not args:
        return await update.message.reply_text(
            "❗ Usage: `/setname <YourName>`\nExample: `/setname IronLegion`",
            parse_mode=ParseMode.MARKDOWN
        )

    name = args[0].strip()
    if not name.replace("_", "").isalnum():
        return await update.message.reply_text(
            "🚫 Invalid name. Letters, numbers & underscores only."
        )

    rows = get_rows("Players")
    taken = {r[1].strip().lower() for r in rows[1:] if r[1]}
    if name.lower() in taken:
        return await update.message.reply_text(
            f"⚠️ Name *{name}* is taken. Try `{name}X`.",
            parse_mode=ParseMode.MARKDOWN
        )

    # update name & check first-time
    for idx, row in enumerate(rows):
        if idx == 0: continue
        if row[0] == uid:
            first_time = row[1].strip() == ""
            row[1] = name
            # persist name
            update_row("Players", idx, row)

            if first_time:
                # reward +500 energy and mark progress
                energy = int(row[5]) + 500
                row[5] = str(energy)
                row[7] = "step1"
                update_row("Players", idx, row)

                # 1) Confirmation & reward
                await update.message.reply_text(
                    f"✅ Commander name set to *{name}*!\n"
                    "🎁 You’ve earned +500 ⚡ Energy for completing Task 1.",
                    parse_mode=ParseMode.MARKDOWN
                )

                # 2) Next storyline + quest
                text2 = (
                    "🛡️ *You are the last hope of your region.*\n"
                    "Command your base, rebuild power, and rise to dominate.\n\n"
                    "🧾 *Your second task:*\n"
                    "`/build powerplant` – Start generating energy.\n\n"
                    "🎁 *On completion you’ll earn:* +100 ⛏️ Minerals\n"
                    "After that, check `/status` to view your base."
                )
                markup2 = ReplyKeyboardMarkup(
                    [[KeyboardButton("/build powerplant")], [KeyboardButton("/status")]],
                    resize_keyboard=True
                )
                return await update.message.reply_text(text2, parse_mode=ParseMode.MARKDOWN, reply_markup=markup2)

            # if not first_time
            return await update.message.reply_text(
                f"✅ Commander name updated to *{name}*.\nUse /menu to continue.",
                parse_mode=ParseMode.MARKDOWN
            )

    # not registered
    await update.message.reply_text(
        "❗ You need to run `/start` first to register.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("setname", setname)
