from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from utils.decorators import game_command
from sheets_service import get_rows

@game_command
async def whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /whisper <CommanderName> <message> – send a private message to another commander.
    """
    args = context.args
    if len(args) < 2:
        return await update.message.reply_text(
            "❗ Usage: `/whisper <CommanderName> <message>`",
            parse_mode=ParseMode.MARKDOWN
        )
    target_name = args[0]
    message_text = " ".join(args[1:]).strip()
    uid = str(update.effective_user.id)

    # Fetch all players
    players = get_rows("Players")

    # 1) Determine sender's display name
    sender_name = None
    for row in players[1:]:
        if row[0] == uid:
            sender_name = row[1] or update.effective_user.first_name
            break
    if not sender_name:
        sender_name = update.effective_user.first_name

    # 2) Find target user_id by commander name
    target_id = None
    for row in players[1:]:
        if row[1].lower() == target_name.lower():
            target_id = row[0]
            break
    if not target_id:
        return await update.message.reply_text(
            f"❌ Commander *{target_name}* not found.",
            parse_mode=ParseMode.MARKDOWN
        )

    # 3) Send the whisper
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"💬 *Whisper from {sender_name}:* {message_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text(
            f"✅ Whisper sent to *{target_name}*!",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await update.message.reply_text(
            "❌ Could not deliver the whisper. They may have blocked the bot."
        )

handler = CommandHandler("whisper", whisper)
