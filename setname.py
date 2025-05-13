# handlers/setname.py

import time
from datetime import date, timedelta
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import get_rows, update_row
from utils.format_utils import section_header

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setname – show help or set your unique commander name and unlock your first reward.
    """
    uid  = str(update.effective_user.id)
    args = context.args.copy()

    # 0) Help screen
    if not args or args[0].lower() == "help":
        lines = [
            section_header("🆔 Commander Name Setup 🆔", pad_char="=", pad_count=3),
            "",
            "Ready to stake your claim? Use:",
            "",
            "`/setname <YourName>`",
            "",
            "• Only letters, numbers & underscores allowed",
            "• Example: `/setname Iron_Legion`",
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # 1) Validate name
    name = args[0].strip()
    if not name.replace("_", "").isalnum():
        return await update.message.reply_text(
            section_header("🚫 Invalid Name"),
            parse_mode=ParseMode.MARKDOWN
        ).then(
            lambda _: update.message.reply_text(
                "Only letters, numbers, and underscores allowed (no spaces or symbols).",
                parse_mode=ParseMode.MARKDOWN
            )
        )

    # 2) Check uniqueness
    rows  = get_rows("Players")
    header = rows[0]
    taken = {r[1].strip().lower() for r in rows[1:] if len(r) > 1 and r[1].strip()}
    if name.lower() in taken:
        lines = [
            section_header("⚠️ Name Taken"),
            "",
            f"Commander *{name}* is already claimed.",
            "Try something like `/setname {name}_X`"
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # 3) Update player row
    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        if row[0] != uid:
            continue

        # ensure full length
        while len(row) < len(header):
            row.append("")

        original     = row[1].strip()
        first_time   = (original == "")
        row[1]       = name  # set commander_name

        # First-time reward
        if first_time and row[7] != "step1":
            row[5] = str(int(row[5]) + 500)  # +500 energy
            row[7] = "step1"
            update_row("Players", idx, row)

            # 3a) Confirmation & next quest
            lines = [
                section_header("✅ Name Set!"),
                "",
                f"Welcome, Commander *{name}*!",
                "🎁 +500 ⚡ Energy awarded.",
                "",
                section_header("🧾 Next Mission"),
                "`/build powerplant` – Get your energy grid online.",
            ]
            kb = ReplyKeyboardMarkup(
                [[KeyboardButton("/build powerplant")], [KeyboardButton("/status")]],
                resize_keyboard=True
            )
            return await update.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        else:
            # 3b) Name change confirmation
            update_row("Players", idx, row)
            lines = [
                section_header("🔄 Name Updated"),
                "",
                f"Your commander name is now *{name}*. ",
                "",
                "Use `/status` to jump back to your base."
            ]
            kb = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton("📊 View Base Status", callback_data="status")
            )
            return await update.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )

    # 4) If no row found
    await update.message.reply_text(
        section_header("❗ Not Registered"),
        parse_mode=ParseMode.MARKDOWN
    )
    await update.message.reply_text(
        "You need to run `/start` first to register.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("setname", setname)
