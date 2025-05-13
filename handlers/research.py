# handlers/research.py

from datetime import datetime
import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

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
    /research                     → list available techs
    /research start <tech_key>    → start a research project
    /research queue               → view your queue
    /research cancel <tech_key>   → cancel a pending research
    """
    uid = str(update.effective_user.id)
    args = context.args or []

    # ─── Subcommand: start ────────────────────────────────────────────────────
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research start <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        success = start_research(uid, tech_key)
        if success:
            return await update.message.reply_text(
                f"✅ Research *{tech_key}* queued!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            return await update.message.reply_text(
                f"❌ Could not start research *{tech_key}*. Check resources, slots, or prerequisites.",
                parse_mode=ParseMode.MARKDOWN
            )

    # ─── Subcommand: queue ────────────────────────────────────────────────────
    if args and args[0].lower() == "queue":
        queue = get_queue(uid)
        if not queue:
            return await update.message.reply_text(
                "📭 Your research queue is empty."
            )
        lines = [section_header("⏳ Your Research Queue"), ""]
        defs = load_research_defs()
        now = time.time()
        for item in queue:
            info = defs.get(item["key"], {})
            name = info.get("name", item["key"])
            remaining = int(item["end_ts"] - now)
            lines.append(f"• *{name}* — {format_hhmmss(remaining)} left")
        lines.append("")  # blank line before instructions
        lines.append(f"Cancel one with `{code('/research cancel <tech_key>')}`")
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Subcommand: cancel ───────────────────────────────────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/research cancel <tech_key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        tech_key = args[1]
        success = cancel_research(uid, tech_key)
        if success:
            return await update.message.reply_text(
                f"🗑️ Research *{tech_key}* canceled.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            return await update.message.reply_text(
                f"❌ Could not cancel research *{tech_key}*. It may not be in your queue.",
                parse_mode=ParseMode.MARKDOWN
            )

    # ─── Default: list available techs ───────────────────────────────────────
    available = get_available_research(uid)
    if not available:
        return await update.message.reply_text(
            "🔍 No techs available right now. "
            "Try `/research queue` or complete prerequisites.",
            parse_mode=ParseMode.MARKDOWN
        )

    lines = [section_header("🔬 Available Research"), ""]
    defs = load_research_defs()
    for info in available:
        key     = info["key"]
        name    = info["name"]
        tier    = info["tier"]
        cost    = f"{info['cost_c']}💳 {info['cost_m']}⛏️ {info['cost_e']}⚡"
        time_str= format_hhmmss(info["time_sec"])
        prereqs = ", ".join(info["prereqs"]) if info["prereqs"] else "None"
        lines.append(
            f"*{name}* (`{key}`) — Tier {tier}\n"
            f"Cost: {cost} | Time: {time_str}\n"
            f"Prereqs: {prereqs}\n"
        )
    lines.append("")  # blank before instructions
    lines.append(f"Start one with `{code('/research start <tech_key>')}`")

    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler("research", research)
