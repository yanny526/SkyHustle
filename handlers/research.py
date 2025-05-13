from datetime import datetime
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.research_manager import (
    get_available_research,
    start_research,
    get_queue,
    load_research_defs,
    cancel_research,
)
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header, code

async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /research                 → list available techs
    /research start <key>     → start a research project
    /research queue           → view your queue (with cancel buttons)
    /research cancel <key>    → cancel a queued research
    """
    uid  = str(update.effective_user.id)
    args = context.args or []

    # ─── Start ──────────────────────────────
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research start <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        ok = start_research(uid, args[1])
        return await update.message.reply_text(
            f"{'✅' if ok else '❌'} "
            + (f"Research *{args[1]}* queued!" if ok else f"Could not start *{args[1]}*."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Cancel via text ────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research cancel <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        ok = cancel_research(uid, args[1])
        return await update.message.reply_text(
            f"{'✅' if ok else '❌'} "
            + (f"Cancelled *{args[1]}*." if ok else f"Failed to cancel *{args[1]}*."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Queue w/ inline buttons ───────────
    if args and args[0].lower() == "queue":
        queue = get_queue(uid)
        if not queue:
            return await update.message.reply_text("📭 Your research queue is empty.")
        defs = load_research_defs()
        now  = time.time()

        lines = [section_header("⏳ Your Research Queue"), ""]
        buttons = []
        for item in queue:
            info      = defs.get(item["key"], {})
            name      = info.get("name", item["key"])
            remaining = max(0, int(item["end_ts"] - now))
            lines.append(f"*{name}* — {format_hhmmss(remaining)} left")
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ Cancel {name}",
                    callback_data=f"research_cancel:{item['key']}"
                )
            ])

        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ─── List available ────────────────────
    available = get_available_research(uid)
    if not available:
        return await update.message.reply_text(
            "🔍 No techs available right now. Check /research queue or complete prerequisites.",
            parse_mode=ParseMode.MARKDOWN
        )

    defs  = load_research_defs()
    lines = [section_header("🔬 Available Research"), ""]
    for info in available:
        cost    = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        tstr    = format_hhmmss(info["time_sec"])
        prereqs = ", ".join(info["prereqs"]) or "None"
        lines.append(
            f"*{info['name']}* (`{info['key']}`) — Tier {info['tier']}\n"
            f"Cost: {cost} | Time: {tstr}\n"
            f"Prereqs: {prereqs}\n"
        )
    lines.append("Start one with `/research start <tech_key>`")
    lines.append("Or cancel a queued one with `/research cancel <tech_key>`")

    return await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.MARKDOWN
    )

async def research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline “Cancel” button presses for research.
    """
    query = update.callback_query
    await query.answer()  # acknowledge tap
    _, tech_key = query.data.split(":", 1)
    ok = cancel_research(str(update.effective_user.id), tech_key)
    # pop up a small alert
    await query.answer(
        text=f"{'✅' if ok else '❌'} "
             + (f"Cancelled {tech_key}" if ok else f"Failed to cancel {tech_key}"),
        show_alert=True
    )
    # re-render the queue in place
    context.args = ["queue"]
    await research(update, context)

handler          = CommandHandler("research", research)
callback_handler = CallbackQueryHandler(research_callback, pattern=r"^research_cancel:")
