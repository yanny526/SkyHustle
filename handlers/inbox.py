from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows
from modules.whisper_manager import fetch_recent_whispers

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /inbox – view your recent private messages (last 5).
    """
    uid = str(update.effective_user.id)
    msgs = fetch_recent_whispers(uid)
    if not msgs:
        return await update.message.reply_text("📭 No private messages.")

    # map user IDs to commander names
    players = {r[0]: r[1] for r in get_rows("Players")[1:]}
    lines = ["📬 *Your Recent Whispers:*"]
    for sender, recipient, ts, text in msgs:
        direction = "From" if recipient == uid else "To"
        other_id  = sender if recipient == uid else recipient
        other_name = players.get(other_id, "Unknown")
        # make timestamp prettier
        when = ts.replace("T", " ")[:19]
        lines.append(f"{when} | {direction} *{other_name}*: {text}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler("inbox", inbox)
