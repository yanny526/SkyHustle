import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.building_manager import (
    get_available_builds,
    get_build_defs,
    start_build,
    get_build_queue,
    cancel_build,
    _complete_single_build,
    update_build_progress,
)
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header, code

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build                    → list all buildings (locked/affordable/done)
    /build start <key>        → queue an upgrade (schedules notification + inline progress)
    /build queue              → view pending upgrades
    /build cancel <key>       → cancel a queued upgrade
    """
    uid = str(update.effective_user.id)
    args = context.args or []

    # ── start a build, send initial progress, schedule updates & completion ────
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/build start <key>')}",
                parse_mode=ParseMode.MARKDOWN
            )

        key = args[1]
        ok = start_build(uid, key)
        if not ok:
            return await update.message.reply_text(
                f"❌ Cannot queue `{key}`.",
                parse_mode=ParseMode.MARKDOWN
            )

        # fetch build duration
        defs  = get_build_defs()
        info  = defs.get(key, {})
        dur   = info.get("time_sec", 0)

        # timestamps
        start_ts = time.time()
        end_ts   = start_ts + dur

        # send initial message (0% progress)
        name      = info.get("name", key)
        bar       = "▁" * 10
        left_str  = format_hhmmss(dur)
        init_text = f"🏗️ Building *{name}* |{bar}| 0% — {left_str} left"
        msg = await update.message.reply_text(
            init_text,
            parse_mode=ParseMode.MARKDOWN
        )

        # schedule repeating inline progress updates
        interval = max(int(dur / 10), 1)  # at most 10 updates
        context.job_queue.run_repeating(
            update_build_progress,
            interval=interval,
            first=interval,
            name=f"progress_{uid}_{key}",
            data={
                "chat_id":      msg.chat_id,
                "message_id":   msg.message_id,
                "start_ts":     start_ts,
                "end_ts":       end_ts,
                "key":          key,
                "name":         name,
            }
        )

        # schedule final completion notification
        context.job_queue.run_once(
            _complete_single_build,
            dur,
            data={"user_id": uid, "key": key},
            name=f"build_{uid}_{key}"
        )
        return  # done

    # ── cancel a queued build ─────────────────────────────────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/build cancel <key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        key = args[1]
        ok  = cancel_build(uid, key)
        # remove any scheduled jobs
        for job in context.job_queue.get_jobs_by_name(f"build_{uid}_{key}"):
            job.schedule_removal()
        for job in context.job_queue.get_jobs_by_name(f"progress_{uid}_{key}"):
            job.schedule_removal()

        return await update.message.reply_text(
            ("✅" if ok else "❌") + (f" Cancelled `{key}`." if ok else f" Failed to cancel `{key}`."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ── list pending builds ────────────────────────────────────────────────────
    if args and args[0].lower() == "queue":
        q = get_build_queue(uid)
        if not q:
            return await update.message.reply_text("📭 Your build queue is empty.")
        defs = {b["key"]: b for b in get_available_builds(uid)}
        now  = time.time()

        lines, buttons = [section_header("⏳ Your Build Queue"), ""], []
        for item in q:
            info = defs.get(item["key"], {})
            name = info.get("name", item["key"])
            left = max(0, int(item["end_ts"] - now))
            lines.append(f"*{name}* — {format_hhmmss(left)} left")
            buttons.append([
                InlineKeyboardButton(f"❌ Cancel {name}", callback_data=f"build_cancel:{item['key']}")
            ])

        markup = InlineKeyboardMarkup(buttons)
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )

    # ── default: list all available builds ─────────────────────────────────────
    allb = get_available_builds(uid)
    lines = [section_header("🏗️ Available Buildings"), ""]
    for b in allb:
        key, name, tier = b["key"], b["name"], b["tier"]
        status = (
            "✅ Done" if b["done"]
            else "🔒 Locked" if b["locked"]
            else "💰 Affordable" if b["affordable"]
            else "❌ Too Expensive"
        )
        costs = f"{b['cost_c']}💳 {b['cost_m']}⛏️ {b['cost_e']}⚡"
        lines.append(
            f"*{name}* (`{key}`) — Tier {tier} — _{status}_\n"
            f"Cost: {costs} | Time: {format_hhmmss(b['time_sec'])}\n"
        )
    lines.append("Queue one with `/build start <key>`")
    lines.append("Or cancel with `/build cancel <key>`")

    return await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

async def build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query
    _, key  = q.data.split(":", 1)
    await q.answer()
    ok      = cancel_build(str(update.effective_user.id), key)

    # remove scheduled jobs
    for job in context.job_queue.get_jobs_by_name(f"build_{update.effective_user.id}_{key}"):
        job.schedule_removal()
    for job in context.job_queue.get_jobs_by_name(f"progress_{update.effective_user.id}_{key}"):
        job.schedule_removal()

    await q.answer(
        text=("✅" if ok else "❌") + (f" Cancelled `{key}`." if ok else "Failed"),
        show_alert=True
    )

    # refresh queue view
    context.args = ["queue"]
    await build(update, context)

handler          = CommandHandler("build", build)
callback_handler = CallbackQueryHandler(build_callback, pattern=r"^build_cancel:")
