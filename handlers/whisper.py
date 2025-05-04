from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from modules.whisper_manager import record_whisper

@game_command  # if you want resource ticks/upgrades before whisper
async def whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /whisper <CommanderName> <message> – send a private message.
    """
    user = update.effective_user
    uid = str(user.id)
    args = context.args

    if len(args) < 2:
        return await update.message.reply_text(
            "❗ Usage: `/whisper <CommanderName> <message>`",
            parse_mode=ParseMode.MARKDOWN
        )

    target_name = args[0]
    message_text = " ".join(args[1:])

    # look up target ID
    players = get_rows("Players")[1:]
    target_row = next((r for r in players if r[1].lower() == target_name.lower()), None)
    if not target_row:
        return await update.message.reply_text(
            f"❌ Commander *{target_name}* not found.",
            parse_mode=ParseMode.MARKDOWN
        )

    recipient_id = target_row[0]

    # 1) send confirmation to sender
    await update.message.reply_text(
        f"🤫 Sent to *{target_name}*: {message_text}",
        parse_mode=ParseMode.MARKDOWN
    )

    # 2) notify recipient
    await context.bot.send_message(
        chat_id=int(recipient_id),
        text=f"💌 Whisper from *{user.first_name}*: {message_text}",
        parse_mode=ParseMode.MARKDOWN
    )

    # 3) record & prune
    record_whisper(uid, recipient_id, message_text)

handler = CommandHandler("whisper", whisper)
