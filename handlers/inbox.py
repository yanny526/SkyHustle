# handlers/inbox.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.whisper_manager import fetch_recent_whispers
from utils.format_utils import section_header

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /inbox            → show help & examples
    /inbox            → view your recent private messages (last 5)
    """
    uid  = str(update.effective_user.id)
    args = context.args

    # 0) Help screen
    if args and args[0].lower() == "help":
        lines = [
            section_header("✉️ INBOX HELP ✉️", pad_char="=", pad_count=3),
            "",
            "Keep track of your whispers:",
            "",
            section_header("📬 View Messages", pad_char="-", pad_count=3),
            "`/inbox`",
            "→ Show your last 5 private messages.",
            "",
            section_header("💬 Send a Whisper", pad_char="-", pad_count=3),
            "`/whisper CommanderName Your message here`",
            "→ Send a private message to another commander.",
            "",
            "Use `/inbox` anytime to check for new whispers!",
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # 1) Fetch recent whispers
    whispers = fetch_recent_whispers(uid)
    if not whispers:
        text = "\n".join([
            section_header("📭 Your Inbox", pad_char="=", pad_count=3),
            "",
            "Nothing here — no new messages!",
            "",
            "Send a whisper with `/whisper CommanderName Hello there!`"
        ])
        return await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # 2) Build message list
    lines = [section_header("📬 Your Recent Whispers", pad_char="=", pad_count=3), ""]
    for sender_id, sender_name, recipient_id, recipient_name, ts, text in whispers:
        # Format timestamp
        when = ts.replace("T", " ")[:19]
        if recipient_id == uid:
            # received
            lines.append(f"{when} | From *{sender_name}*: {text}")
        else:
            # sent
            lines.append(f"{when} | To *{recipient_name}*: {text}")
    lines.append("")
    lines.append("Type `/inbox help` for more options.")

    # 3) Reply
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("inbox", inbox)
