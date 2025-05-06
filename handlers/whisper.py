# handlers/whisper.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from utils.decorators import game_command
from utils.format_utils import section_header, code
from sheets_service import get_rows
from modules.whisper_manager import record_whisper, fetch_recent_whispers

@game_command  # ensure game state is up to date before sending
async def whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /whisper – show help or send a private message to another commander.
    """
    uid  = str(update.effective_user.id)
    args = context.args.copy()

    # 0) Help screen
    if not args or args[0].lower() == "help":
        lines = [
            section_header("💬 Whisper Help", pad_char="=", pad_count=3),
            "",
            "Send a secret message to another commander:",
            "",
            section_header("✉️ Usage", pad_char="-", pad_count=3),
            f"{code('/whisper')} <CommanderName> <message>",
            "",
            section_header("🔍 Example", pad_char="-", pad_count=3),
            f"{code('/whisper IronLegion')} Meet at the north ridge at dawn!",
            "",
            "View your inbox with `/inbox`.",
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # 1) Validate arguments
    if len(args) < 2:
        return await update.message.reply_text(
            f"❗ Usage: {code('/whisper')} <CommanderName> <message>",
            parse_mode=ParseMode.MARKDOWN
        )

    target_name  = args[0]
    message_text = " ".join(args[1:]).strip()

    # 2) Locate recipient
    players = get_rows("Players")[1:]
    recipient_id = None
    for row in players:
        if row[1].lower() == target_name.lower():
            recipient_id = row[0]
            break

    if not recipient_id:
        lines = [
            section_header("🚫 Commander Not Found"),
            "",
            f"No commander named *{target_name}* was found.",
            "Check spelling or use `/inbox` to see recent whispers."
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # 3) Record and confirm
    record_whisper(uid, recipient_id, message_text)
    lines = [
        section_header("🤫 Whisper Sent!"),
        "",
        f"Your message to *{target_name}* has been delivered.",
        "",
        section_header("📬 Next Steps", pad_char="-", pad_count=3),
        f"• View replies with {code('/inbox')}",
        f"• Send another with {code('/whisper <Commander> <msg>')}"
    ]
    kb = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("📬 Go to Inbox", callback_data="inbox"),
        InlineKeyboardButton("💬 New Whisper", callback_data="whisper_help")
    ])
    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

async def whisper_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # handle inline buttons: "inbox" or "whisper_help"
    data = update.callback_query.data
    if data == "inbox":
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="",  # trigger /inbox
            reply_markup=None,
            parse_mode=ParseMode.MARKDOWN
        ).then(lambda _: context.bot.invoke_command('/inbox'))
    if data == "whisper_help":
        return await whisper(update, context)

handler          = CommandHandler("whisper", whisper)
callback_handler = CallbackQueryHandler(whisper_button, pattern="^(inbox|whisper_help)$")
