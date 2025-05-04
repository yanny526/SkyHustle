# handlers/reports.py

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports – list your pending scouts & attacks (or show a friendly no-pending message).
    """
    chat_id = update.effective_chat.id
    pending = context.chat_data.get("pending", [])
    now     = datetime.utcnow()

    lines = []
    for job_name in pending:
        jobs = context.job_queue.get_jobs_by_name(job_name)
        if not jobs:
            continue
        job = jobs[0]
        delta = job.next_run_time - now
        mins, secs = divmod(int(delta.total_seconds()), 60)

        target = job_name.split("_")[2]  # format: scout_uid_target_ts
        if job_name.startswith("scout_"):
            lines.append(f"🔎 Scouts → *{target}* in {mins}m {secs}s")
        elif job_name.startswith("attack_"):
            lines.append(f"🏹 Attack → *{target}* in {mins}m {secs}s")

    if not lines:
        text = "🗒️ *No pending operations.*"
    else:
        text = "🗒️ *Your Pending Operations:*\n" + "\n".join(lines)

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


handler          = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
