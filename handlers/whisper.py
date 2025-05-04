# handlers/whisper.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from utils.decorators import game_command
from sheets_service import get_rows
from modules.whisper_manager import record_whisper, fetch_recent_whispers

@game_command  # tick resources or process upgrades before whisper
async def whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /whisper <CommanderName> <message> – send a private message to another commander.
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
    message_text = " ".join(args[1:]).strip()

    # find recipient
    rows = get_rows('Players')[1:]
    recipient_id = None
    for row in rows:
        if row[1].lower() == target_name.lower():
            recipient_id = row[0]
            break

    if not recipient_id:
        return await update.message.reply_text(
            f"❌ Commander *{target_name}* not found.",
            parse_mode=ParseMode.MARKDOWN
        )

    # record whisper
    record_whisper(uid, recipient_id, message_text)

    await update.message.reply_text(
        f"🤫 Whisper sent to *{target_name}*!", parse_mode=ParseMode.MARKDOWN
    )

# View recent whispers (also covered by /inbox)
async def whisper_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Internal helper to send real-time incoming whispers.
    """
    # This could be called by your whisper_manager when a message arrives
    update.message.reply_text(update.callback_query.data)

handler = CommandHandler('whisper', whisper)
