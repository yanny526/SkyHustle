# handlers/announce.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.admin_manager import is_admin
from sheets_service import get_rows, append_row
from utils.format_utils import section_header, code

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /announce – broadcast a message to all players (admin only).
    """
    uid  = str(update.effective_user.id)
    args = context.args or []

    # ─── Help Screen ─────────────────────────────────────────────────────────
    if not args or args[0].lower() == "help":
        lines = [
            section_header("📣 Announcement Help 📣", pad_char="=", pad_count=3),
            "",
            "Admins can broadcast a message to all commanders:",
            "",
            section_header("💬 Usage", pad_char="-", pad_count=3),
            f"{code('/announce')} <your message here>",
            "",
            "Example:",
            f"{code('/announce')} Prepare for the Chaos Storm at midnight!",
        ]
        kb = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("🏠 Back to Help", callback_data="help")
        )
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )

    # ─── Permission Check ─────────────────────────────────────────────────────
    if not is_admin(uid):
        text = section_header("❌ Unauthorized", pad_char="=", pad_count=3) + "\n\nYou are not allowed to use this command."
        return await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # ─── Extract & Broadcast ─────────────────────────────────────────────────
    announcement = " ".join(args).strip()
    players = get_rows("Players")[1:]
    uids    = [r[0] for r in players if r and r[0]]

    sent, failed = 0, 0
    for pid in uids:
        try:
            await context.bot.send_message(chat_id=int(pid), text=announcement)
            sent += 1
        except:
            failed += 1

    # ─── Log Announcement ────────────────────────────────────────────────────
    timestamp = datetime.utcnow().isoformat()
    append_row("Administrators", [uid, timestamp, announcement])

    # ─── Confirmation UI ──────────────────────────────────────────────────────
    lines = [
        section_header("📣 Announcement Sent", pad_char="=", pad_count=3),
        "",
        f"Message: _{announcement}_",
        f"✅ Sent to {sent} commanders" + (f", ⚠️ {failed} failed" if failed else ""),
    ]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 New Announcement", callback_data="announce_help")],
        [InlineKeyboardButton("🏠 Help Menu", callback_data="help")]
    ])

    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

async def announce_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "announce_help":
        # simulate /announce help
        fake_update = update
        fake_update.message = update.callback_query.message
        fake_update.callback_query = None
        return await announce(fake_update, context)

handler          = CommandHandler("announce", announce)
callback_handler = CallbackQueryHandler(announce_button, pattern="^announce_help$")
