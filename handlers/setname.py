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
    /setname - show help or set your unique commander name, advance tutorial progress, and unlock your first reward.
    """
    uid = str(update.effective_user.id)
    args = context.args.copy()

    # Help screen
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

    # Fetch players and header
    rows = get_rows("Players")
    if not rows:
        return
    header = rows[0]
    def idx(col):
        return header.index(col) if col in header else None

    name_idx = idx("commander_name")
    progress_idx = idx("progress")
    energy_idx = idx("energy")

    # Validate name
    name = args[0].strip()
    if not name.replace("_", "").isalnum():
        return await update.message.reply_text(
            section_header("🚫 Invalid Name", pad_char="=", pad_count=3),
            parse_mode=ParseMode.MARKDOWN
        )

    # Check uniqueness
    taken = {
        r[name_idx].strip().lower()
        for r in rows[1:]
        if len(r) > name_idx and r[name_idx]
    }
    if name.lower() in taken:
        lines = [
            section_header("⚠️ Name Taken", pad_char="=", pad_count=3),
            "",
            f"Commander *{name}* is already claimed.",
            f"Try something like `/setname {name}_X`"
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # Update player row
    for ri, row in enumerate(rows[1:], start=1):
        if row[0] != uid:
            continue

        # Ensure full length
        while len(row) < len(header):
            row.append("")

        original = row[name_idx].strip()
        first_time = (original == "")

        # Set name
        row[name_idx] = name

        # Tutorial progression: step 1 -> step 2
        if first_time and progress_idx is not None and row[progress_idx] == "1":
            # +500 energy reward
            if energy_idx is not None and row[energy_idx].isdigit():
                row[energy_idx] = str(int(row[energy_idx]) + 500)
            # advance to step 2
            row[progress_idx] = "2"

            update_row("Players", ri, row)

            # Send confirmation and next tutorial step
            lines = [
                section_header("✅ Name Set!", pad_char="=", pad_count=3),
                "",
                f"Welcome, Commander *{name}*!",
                "🎁 +500 ⚡ Energy awarded.",
                "",
                section_header("🧾 Tutorial Step 2", pad_char="-", pad_count=3),
                "`/build powerplant` — Get your energy grid online.",
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

        # Subsequent name changes or tutorial already passed
        update_row("Players", ri, row)
        lines = [
            section_header("🔄 Name Updated", pad_char="=", pad_count=3),
            "",
            f"Your commander name is now *{name}*.",
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

    # If no row found
    await update.message.reply_text(
        section_header("❗ Not Registered", pad_char="=", pad_count=3),
        parse_mode=ParseMode.MARKDOWN
    )
    await update.message.reply_text(
        "You need to run `/start` first to register.",
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("setname", setname)
