# handlers/reports.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports – list your pending scouts & attacks
    Also handles the “📜 View Pending” button.
    """
    user_id = str(update.effective_user.id)
    now = datetime.utcnow()

    jobs = context.application.job_queue.get_jobs()
    lines = []
    for job in jobs:
        data = job.data or {}
        if data.get("uid") != user_id:
            continue

        # Compute time until execution
        run_at = job.next_run_time  # datetime in UTC
        delta = run_at - now
        mins, secs = divmod(int(delta.total_seconds()), 60)
        when = f"in {mins}m {secs}s"

        name = job.name
        if name.startswith("scout_"):
            lines.append(f"🔎 Scouts → *{data['defender_name']}* {when}")
        elif name.startswith("attack_"):
            lines.append(f"🏹 Attack → *{data['defender_name']}* {when}")

    if not lines:
        text = "🗒️ *No pending operations.*"
    else:
        text = "🗒️ *Your Pending Operations:*\n" + "\n".join(lines)

    # Offer a refresh button
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def reports_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await reports(update, context)

# Export handlers
handler        = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
