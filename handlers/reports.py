from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from modules.unit_manager import UNITS

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reports – list your pending scouts & attacks (or show a friendly no-pending message).
    """
    chat_id = update.effective_chat.id
    pending = context.chat_data.get("pending", [])
    now     = datetime.now(timezone.utc)

    lines = []
    for job_name in pending:
        jobs = context.job_queue.get_jobs_by_name(job_name)
        if not jobs:
            continue
        job = jobs[0]
        delta = job.next_run_time - now
        mins, secs = divmod(int(delta.total_seconds()), 60)
        target = job_name.split("_")[2]

        data = job.data or {}
        if job_name.startswith("scout_"):
            lines.append(f"🔎 Scouts → *{target}* in {mins}m {secs}s")
        elif job_name.startswith("attack_"):
            comp = data.get("composition", {})
            comp_str = " ".join(f"{UNITS[k][1]}×{v}" for k, v in comp.items())
            lines.append(
                f"🏹 Attack → *{target}* [{comp_str}] in {mins}m {secs}s"
            )

    text = "🗒️ *No pending operations.*" if not lines else "🗒️ *Pending Operations:*\n" + "\n".join(lines)

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="reports")
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

async def reports_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await reports(update, context)

handler          = CommandHandler("reports", reports)
callback_handler = CallbackQueryHandler(reports_button, pattern="^reports$")
