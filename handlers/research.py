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
from utils.format_utils import section_header_html, code_html

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
                f"Usage: {code_html('/research start <tech_key>')}",
                parse_mode=ParseMode.HTML
            )
        tech_key = args[1]
        ok = start_research(uid, tech_key)
        return await update.message.reply_text(
            ("✅ Research <b>{}</b> queued!" if ok else "❌ Could not start <b>{}</b>.").format(tech_key),
            parse_mode=ParseMode.HTML
        )

    # ─── Cancel a queued research ───────────────────────────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code_html('/research cancel <tech_key>')}",
                parse_mode=ParseMode.HTML
            )
        tech_key = args[1]
        ok = cancel_research(uid, tech_key)
        return await update.message.reply_text(
            ("✅ Cancelled <b>{}</b>." if ok else "❌ Failed to cancel <b>{}</b>.").format(tech_key),
            parse_mode=ParseMode.HTML
        )

    # ─── Show queue with “Cancel” buttons ──────────────────────────────────
    if args and args[0].lower() == "queue":
        queue = get_queue(uid)
        if not queue:
            return await update.message.reply_text(
                "📭 Your research queue is empty.",
                parse_mode=ParseMode.HTML
            )
        defs = load_research_defs()
        now  = time.time()

        text_lines = [section_header_html("⏳ Your Research Queue"), ""]
        buttons = []
        for item in queue:
            info      = defs.get(item["key"], {})
            name      = info.get("name", item["key"])
            remaining = max(0, int(item["end_ts"] - now))
            text_lines.append(f"<b>{name}</b> — {format_hhmmss(remaining)} left")
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ Cancel {name}",
                    callback_data=f"research_cancel:{item['key']}"
                )
            ])

        return await update.message.reply_text(
            "\n".join(text_lines),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    # ─── Default: list all available techs ─────────────────────────────────
    available = get_available_research(uid)
    if not available:
        return await update.message.reply_text(
            "🔍 No techs available right now. Check <b>/research queue</b> or complete prerequisites.",
            parse_mode=ParseMode.HTML
        )

    defs  = load_research_defs()
    text_lines = [section_header_html("🔬 Available Research"), ""]
    for info in available:
        key     = info["key"]
        name    = info["name"]
        tier    = info["tier"]
        cost    = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        tstr    = format_hhmmss(info["time_sec"])
        prereqs = ", ".join(info["prereqs"]) if info["prereqs"] else "None"

        text_lines.append(
            f"<b>{name}</b> (<code>{key}</code>) — Tier {tier}\n"
            f"Cost: {cost} | Time: {tstr}\n"
            f"Prereqs: {prereqs}\n"
        )

    text_lines.append(f"Start one with {code_html('/research start <tech_key>')}")
    text_lines.append(f"Or cancel a queued one with {code_html('/research cancel <tech_key>')}")

    return await update.message.reply_text(
        "\n".join(text_lines),
        parse_mode=ParseMode.HTML
    )


async def research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline “Cancel” button presses for research.
    """
    query = update.callback_query
    await query.answer()
    _, tech_key = query.data.split(":", 1)

    ok = cancel_research(str(update.effective_user.id), tech_key)
    # feedback
    await query.answer(
        text=("✅" if ok else "❌") + f" {'Cancelled' if ok else 'Failed to cancel'} <b>{tech_key}</b>",
        show_alert=True
    )

    # refresh in-place
    context.args = ["queue"]
    # use edit_message_text instead of a fresh reply
    await query.edit_message_text(
        text=(await research(update, context)).text,
        parse_mode=ParseMode.HTML,
        reply_markup=update.callback_query.message.reply_markup
    )


handler          = CommandHandler("research", research)
callback_handler = CallbackQueryHandler(research_callback, pattern=r"^research_cancel:")
