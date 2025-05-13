# handlers/research.py

import time
from datetime import datetime
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
    /research                 → list available techs with Start/Info buttons
    /research start <key>     → start a research project
    /research queue           → view your queue
    /research cancel <key>    → cancel a queued research
    """
    uid  = str(update.effective_user.id)
    args = context.args or []

    # ─── /research start <key> ───────────────────────────────────────────────
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

    # ─── /research cancel <key> ──────────────────────────────────────────────
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

    # ─── /research queue ────────────────────────────────────────────────────
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

    # ─── Default /research → list all available techs with buttons ──────────
    available = get_available_research(uid)
    defs      = load_research_defs()
    now       = time.time()

    if not defs:
        return await update.message.reply_text(
            "🔍 Unable to load tech definitions right now.",
            parse_mode=ParseMode.MARKDOWN
        )

    # Build the list header
    if not available:
        header = section_header("🔒 Research Locked / Coming Soon")
    else:
        header = section_header("🔬 Available Research")
    lines = [header, ""]

    # Build buttons: two per row (Start / Info)
    buttons = []
    for info in defs.values():
        key  = info["key"]
        name = info.get("name", key)
        tier = info.get("tier", 1)
        time_sec = info.get("time_sec", 0)

        # Always show item, but style locked ones differently
        locked = key not in {i["key"] for i in available}
        emoji = "🔒" if locked else "🔬"
        cost    = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        tstr    = format_hhmmss(time_sec)
        prereqs = ", ".join(info["prereqs"]) if info["prereqs"] else "None"

        lines.append(
            f"{emoji} *{name}* (`{key}`) — Tier {tier}\n"
            f"Cost: {cost} | Time: {tstr}\n"
            f"Prereqs: {prereqs}\n"
        )

        # Buttons row
        btns = []
        # Start button (disabled if locked)
        btns.append(
            InlineKeyboardButton(
                text="🔬 Start",
                callback_data=f"research_start:{key}",
                # you can append `,disabled=True` if you want to show disabled state in UI libraries that support it
            )
        )
        # Info button
        btns.append(
            InlineKeyboardButton(
                text="ℹ️ Info",
                callback_data=f"research_info:{key}"
            )
        )
        buttons.append(btns)

    markup = InlineKeyboardMarkup(buttons)
    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

async def research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline buttons:
     - research_start:<key>
     - research_info:<key>
     - research_cancel:<key>
    """
    query = update.callback_query
    await query.answer()  # dismiss loading
    data = query.data  # e.g. "research_start:ai_boost"

    cmd, key = data.split(":", 1)
    uid = str(update.effective_user.id)

    if cmd == "research_start":
        ok = start_research(uid, key)
        await query.answer(
            text=f"{'✅' if ok else '❌'} "
                 + (f"Queued {key}" if ok else f"Cannot queue {key}"),
            show_alert=True
        )

    elif cmd == "research_cancel":
        ok = cancel_research(uid, key)
        await query.answer(
            text=f"{'✅' if ok else '❌'} "
                 + (f"Cancelled {key}" if ok else f"Cannot cancel {key}"),
            show_alert=True
        )

    elif cmd == "research_info":
        defs = load_research_defs()
        info = defs.get(key)
        if not info:
            await query.answer(text="❌ Unknown tech", show_alert=True)
        else:
            prereqs = ", ".join(info["prereqs"]) if info["prereqs"] else "None"
            msg = (
                f"*{info['name']}* (`{key}`)\n"
                f"Tier: {info['tier']}\n"
                f"Cost: {info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡\n"
                f"Time: {format_hhmmss(info['time_sec'])}\n"
                f"Prereqs: {prereqs}"
            )
            await query.answer(text=msg, show_alert=True)

    # After handling, refresh the list in-place:
    # simulate a fresh `/research` on this very message
    context.args = []  # go back to default list view
    # edit original message
    await research(update, context)

# Register both handlers
handler          = CommandHandler("research", research)
callback_handler = CallbackQueryHandler(research_callback, pattern=r"^research_")
