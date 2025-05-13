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
    uid  = str(update.effective_user.id)
    args = context.args or []

    # ─── Start ───────────────────────────────────────────────────────────────
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research start <tech_key>')}", parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        ok = start_research(uid, tech_key)
        return await update.message.reply_text(
            f"{'✅' if ok else '❌'} "
            + (f"Research *{tech_key}* queued!" if ok else f"Could not start *{tech_key}*."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Cancel (text command) ────────────────────────────────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research cancel <tech_key>')}", parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        ok = cancel_research(uid, tech_key)
        return await update.message.reply_text(
            f"{'✅' if ok else '❌'} "
            + (f"Cancelled *{tech_key}*." if ok else f"Failed to cancel *{tech_key}*."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Queue (text command) ────────────────────────────────────────────────
    if args and args[0].lower() == "queue":
        queue = get_queue(uid)
        if not queue:
            return await update.message.reply_text("📭 Your research queue is empty.")
        defs   = load_research_defs()
        now    = time.time()
        lines  = [section_header("⏳ Your Research Queue"), ""]
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

    # ─── Default: list available techs ────────────────────────────────────────
    available = get_available_research(uid)
    if not available:
        return await update.message.reply_text(
            "🔍 No techs available right now. Check /research queue or complete prerequisites.",
            parse_mode=ParseMode.MARKDOWN
        )

    defs  = load_research_defs()
    lines = [section_header("🔬 Available Research"), ""]
    for info in available:
        key     = info["key"]
        name    = info["name"]
        tier    = info["tier"]
        cost    = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        tstr    = format_hhmmss(info["time_sec"])
        prereqs = ", ".join(info["prereqs"]) or "None"
        lines.append(
            f"*{name}* (`{key}`) — Tier {tier}\n"
            f"Cost: {cost} | Time: {tstr}\n"
            f"Prereqs: {prereqs}\n"
        )
    lines.append("Start one with `/research start <tech_key>`")
    lines.append("Or cancel a queued one with `/research cancel <tech_key>`")
    lines.append("Or check queued researches with `/research queue <tech_key>`")

    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

async def research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # ACK the tap
    _, tech_key = query.data.split(":", 1)

    ok = cancel_research(str(query.from_user.id), tech_key)

    # show a small alert
    await query.answer(
        text=f"{'✅' if ok else '❌'} "
             + (f"Cancelled {tech_key}" if ok else f"Failed to cancel {tech_key}"),
        show_alert=True
    )

    # now re-build the queue display _in place_
    uid   = str(query.from_user.id)
    queue = get_queue(uid)
    if not queue:
        return await query.message.edit_text("📭 Your research queue is empty.")

    defs    = load_research_defs()
    now     = time.time()
    lines   = [section_header("⏳ Your Research Queue"), ""]
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
    await query.message.edit_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

handler          = CommandHandler("research", research)
callback_handler = CallbackQueryHandler(research_callback, pattern=r"^research_cancel:")
