# handlers/notifications.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, JobQueue

from utils.format import section_header

async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    player_id = job.data

    # Retrieve player data
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == player_id:
            commander = row[1]
            credits = row[2]
            minerals = row[3]
            energy = row[4]
            break

    await context.send_message(
        chat_id=player_id,
        text=f"{section_header('NOTIFICATION', '🔔', 'yellow')}\n\n"
             f"Your resources are low!\n"
             f"Credits: {credits}💰 | Minerals: {minerals}⛏️ | Energy: {energy}⚡\n\n"
             f"Use /shop to purchase resource boosts!",
        parse_mode="Markdown"
    )

async def set_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id

    # Remove existing job if it exists
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # Add new job
    context.job_queue.run_repeating(
        send_notification,
        interval=3600,  # Check every hour
        first=10,
        chat_id=chat_id,
        name=str(chat_id)
    )

    await update.effective_message.reply_text(
        "🔔 *Notification Set* 🔔\n\n"
        "You will receive alerts when your resources are low!",
        parse_mode="Markdown"
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_notification(update, context)
