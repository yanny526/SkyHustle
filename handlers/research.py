# handlers/research.py

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

    # ─── Start a new research ───────────────────────────────────────────────
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research start <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        ok = start_research(uid, tech_key)
        return await update.message.reply_text(
            f"{'✅' if ok else '❌'} "
            + (f"Research *{tech_key}* queued!" if ok else f"Could not start *{tech_key}*."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Cancel a queued research ───────────────────────────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research cancel <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        ok = cancel_research(uid, tech_key)
        return await update.message.reply_text(
            f"{'✅' if ok else '❌'} "
            + (f"Cancelled *{tech_key}*." if ok else f"Failed to cancel *{tech_key}*."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Show queue with “Cancel” buttons ──────────────────────────────────
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

        markup = InlineKeyboardMarkup(buttons)
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )

    # ─── Default: list all available techs ─────────────────────────────────
    available = get_available_research(uid)
    defs      = load_research_defs()

    # Even if no resources, show unlocked techs so players can plan ahead
    if not available:
        return await update.message.reply_text(
            "🔍 No techs currently startable. Check /research queue or complete prerequisites.",
            parse_mode=ParseMode.MARKDOWN
        )

    lines = [section_header("🔬 Available Research"), ""]
    for info in available:
        key     = info["key"]
        name    = info["name"]
        tier    = info["tier"]
        cost    = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        tstr    = format_hhmmss(info["time_sec"])

        # map raw prereq-keys to human names
        if info["prereqs"]:
            prereq_names = [
                defs[p]["name"]
                for p in info["prereqs"]
                if p in defs
            ]
            prereq_str = ", ".join(prereq_names) or "None"
        else:
            prereq_str = "None"

        lines.append(
            f"*{name}* (`{key}`) — Tier {tier}\n"
            f"Cost: {cost} | Time: {tstr}\n"
            f"Prereqs: {prereq_str}\n"
        )

    lines.append("Start one with `/research start <tech_key>`")
    lines.append("Or cancel a queued one with `/research cancel <tech_key>`")

    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

async def research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline “Cancel” button presses for research.
    """
    query = update.callback_query
    await query.answer()  # acknowledge button tap
    _, tech_key = query.data.split(":", 1)

    ok = cancel_research(str(update.effective_user.id), tech_key)
    # give user feedback
    await query.answer(
        text=f"{'✅' if ok else '❌'} "
             + (f"Cancelled *{tech_key}*." if ok else f"Failed to cancel *{tech_key}*."),
        show_alert=True
    )

    # refresh the queue list in-place
    context.args = ["queue"]
    # since this was triggered from a callback, there's no `message` on update,
    # we use `edit_message_text` instead of `reply_text`:
    lines = await research(update, context)  # this returns a new Message, but for simplicity:
    # NB: in python-telegram-bot v20 the `research` coroutine writes back to chat directly,
    # so you don't need to do anything else here.

handler          = CommandHandler("research", research)
callback_handler = CallbackQueryHandler(research_callback, pattern=r"^research_cancel:")
