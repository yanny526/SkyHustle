# handlers/chaos_test.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from sheets_service import get_rows
from modules.chaos_storms_manager import get_random_storm, apply_storm, record_storm
from utils.format_utils import section_header, code

async def chaos_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chaos_test – admin-only trigger for immediate Chaos Storm (or show help).
    """
    uid  = update.effective_user.id
    args = context.args or []

    # ─── Help Screen ─────────────────────────────────────────────────────────
    if args and args[0].lower() == "help":
        lines = [
            section_header("🚨 Chaos Test Help 🚨", pad_char="=", pad_count=3),
            "",
            "Admins can trigger a random Chaos Storm immediately for testing.",
            "",
            section_header("⚙️ Usage", pad_char="-", pad_count=3),
            f"{code('/chaos_test')}",
            "→ Launches a random storm and broadcasts it to all players.",
            "",
            "Use `/chaos` to view the official storm catalog and status."
        ]
        kb = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton("🔄 Back to Help", callback_data="help")
        ])
        if update.message:
            return await update.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        else:
            await update.callback_query.answer()
            return await update.callback_query.edit_message_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )

    # ─── Permission Check ─────────────────────────────────────────────────────
    admins = [int(r[0]) for r in get_rows("Administrators")[1:] if r and r[0].isdigit()]
    if uid not in admins:
        text = section_header("🚫 Unauthorized", pad_char="=", pad_count=3) + "\n\n" \
               "You are not authorized to use this command."
        return await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # ─── Trigger & Broadcast Storm ────────────────────────────────────────────
    storm = get_random_storm()
    apply_storm(storm)
    record_storm(storm["id"])

    header = section_header("🚨🔥 ADMIN-TRIGGERED CHAOS STORM 🔥🚨", pad_char="=", pad_count=3)
    name   = f"{storm['emoji']} *{storm['name'].upper()}* {storm['emoji']}"
    body   = storm["story"]
    footer = "🛡️ Stand ready! This storm was unleashed by command."

    full_text = "\n".join([header, "", name, "", body, "", footer])

    kb = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("📊 View Base Status", callback_data="status"),
        InlineKeyboardButton("🆘 Help Menu", callback_data="help")
    ])

    # Send to all players
    for row in get_rows("Players")[1:]:
        try:
            pid = int(row[0])
            await context.bot.send_message(
                chat_id=pid,
                text=full_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        except:
            continue

    # ─── Confirmation to Admin ────────────────────────────────────────────────
    confirm = (
        section_header("✅ Chaos Test Complete", pad_char="=", pad_count=3)
        + "\n\nA random storm was broadcast to all players."
    )
    return await update.message.reply_text(confirm, parse_mode=ParseMode.MARKDOWN)

async def chaos_test_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "chaos_test":
        return await chaos_test(update, context)
    if data == "chaos_test_help":
        # simulate '/chaos_test help'
        context.args = ["help"]
        return await chaos_test(update, context)

handler          = CommandHandler("chaos_test", chaos_test)
callback_handler = CallbackQueryHandler(chaos_test_button, pattern="^(chaos_test|chaos_test_help)$")
