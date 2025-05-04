from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.whisper_manager import fetch_recent_whispers

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /inbox – view your recent private messages (last 5).
    """
    uid = str(update.effective_user.id)
    whispers = fetch_recent_whispers(uid)
    if not whispers:
        return await update.message.reply_text("📭 No private messages.")

    lines = ["📬 *Your Recent Whispers:*"]
    for sender_id, sender_name, recipient_id, recipient_name, ts, text in whispers:
        # format timestamp
        when = ts.replace("T", " ")[:19]
        if recipient_id == uid:
            # message received
            lines.append(f"{when} | From *{sender_name}*: {text}")
        else:
            # message sent
            lines.append(f"{when} | To *{recipient_name}*: {text}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler("inbox", inbox)
