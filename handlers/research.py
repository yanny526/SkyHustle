# handlers/research.py

from datetime import datetime
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from modules.research_manager import (
    get_available_research,
    start_research,
    get_queue,
    cancel_research,
    load_research_defs
)
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header, code


async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /research              → list available techs
    /research start <key>  → start a research project
    /research queue        → view your queue
    /research cancel <key> → cancel a queued research
    """
    uid = str(update.effective_user.id)
    args = context.args or []

    # Subcommand: start via text
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research start <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        success = start_research(uid, tech_key)
        msg = (
            f"✅ Research *{tech_key}* queued!"
            if success else
            f"❌ Could not start research *{tech_key}*. Check resources, slots, or prerequisites."
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # Subcommand: cancel via text
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research cancel <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        success = cancel_research(uid, tech_key)
        msg = (
            f"✅ Research *{tech_key}* canceled."
            if success else
            f"❌ Could not cancel research *{tech_key}*."
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # Subcommand: queue
    if args and args[0].lower() == "queue":
        queued = get_queue(uid)
        if not queued:
            return await update.message.reply_text("📭 Your research queue is empty.")

        defs = load_research_defs()
        now = time.time()

        lines = [section_header("⏳ Your Research Queue"), ""]
        keyboard = []

        for item in queued:
            key = item["key"]
            info = defs.get(key, {})
            name = info.get("name", key)
            remaining = int(item["end_ts"] - now)
            lines.append(f"• *{name}* — {format_hhmmss(remaining)} left")
            keyboard.append([
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"research:cancel:{key}"
                )
            ])

        lines.append("")  
        lines.append("Or type `/research cancel <tech_key>`")
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Default: list available techs
    available = get_available_research(uid)
    if not available:
        return await update.message.reply_text(
            "🔍 No techs available right now. Check /research queue or complete prerequisites.",
            parse_mode=ParseMode.MARKDOWN
        )

    lines = [section_header("🔬 Available Research"), ""]
    keyboard = []

    for info in available:
        key      = info["key"]
        name     = info["name"]
        tier     = info["tier"]
        cost     = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        time_str = format_hhmmss(info["time_sec"])
        prereqs  = ", ".join(info["prereqs"]) if info["prereqs"] else "None"

        lines.append(
            f"*{name}* (`{key}`) — Tier {tier}\n"
            f"Cost: {cost} | Time: {time_str}\n"
            f"Prereqs: {prereqs}\n"
        )
        keyboard.append([
            InlineKeyboardButton(
                "▶️ Start",
                callback_data=f"research:start:{key}"
            )
        ])

    lines.append("Or tap a button below to start:")
    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def research_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline Start & Cancel button presses."""
    query = update.callback_query
    _, action, key = query.data.split(":", 2)
    uid = str(query.from_user.id)

    if action == "start":
        ok = start_research(uid, key)
        text = f"✅ Research *{key}* queued!" if ok else f"❌ Could not start *{key}*."
    elif action == "cancel":
        ok = cancel_research(uid, key)
        text = f"✅ Research *{key}* canceled." if ok else f"❌ Could not cancel *{key}*."
    else:
        text = "⚠️ Unknown action."

    await query.answer()
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)


# Export handlers
handler          = CommandHandler("research", research)
callback_handler = CallbackQueryHandler(research_button, pattern=r"^research:")
