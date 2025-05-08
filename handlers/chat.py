# handlers/chat.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from utils.format import section_header

async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Usage: `/msg <player_id> <message>`",
            parse_mode="Markdown"
        )
        return

    recipient_id = args[0]
    message = ' '.join(args[1:])

    try:
        await context.send_message(
            chat_id=recipient_id,
            text=f"{section_header('PRIVATE MESSAGE', ✉️', 'none')}\n\n"
                 f"**From**: {update.effective_user.name}\n"
                 f"**Message**: {message}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            f"✉️ *Message Sent!* ✉️\n\n"
            f"Your message has been delivered to {recipient_id}.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            f"Failed to send message: {str(e)}",
            parse_mode="Markdown"
        )

async def alliance_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    message = update.message.text

    # Retrieve player's alliance
    players = get_rows("Players")
    alliance = None
    for row in players[1:]:
        if row[0] == uid and len(row) > 9:
            alliance = row[9]
            break

    if not alliance:
        await update.message.reply_text(
            "You are not part of any alliance. Use /alliance to join or create one.",
            parse_mode="Markdown"
        )
        return

    # Send message to all alliance members
    for row in players[1:]:
        if len(row) > 9 and row[9] == alliance:
            try:
                await context.send_message(
                    chat_id=row[0],
                    text=f"{section_header('ALLIANCE CHAT', '👥', 'none')}\n\n"
                         f"**From**: {update.effective_user.name}\n"
                         f"**Message**: {message}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Failed to send alliance message to {row[0]}: {str(e)}")

    await update.message.reply_text(
        f"👥 *Alliance Message Sent!* 👥\n\n"
        f"Your message has been delivered to your alliance.",
        parse_mode="Markdown"
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await private_message(update, context)

async def alliance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alliance_chat(update, context)
