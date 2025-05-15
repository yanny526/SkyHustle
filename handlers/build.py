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
)
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header, code

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build                    → list all buildings
    /build start <key>        → queue an upgrade (sends ETA & schedules notification)
    /build queue              → view pending upgrades
    /build cancel <key>       → cancel a queued upgrade
    """
    uid  = str(update.effective_user.id)
    args = context.args or []

    # ── start a build and schedule its completion ──────────────────────────────
    if args and args[0].lower() == "start":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/build start <key>')}",
                parse_mode=ParseMode.MARKDOWN
            )

        key = args[1]
        ok  = start_build(uid, key)
        if not ok:
            return await update.message.reply_text(
                f"❌ Cannot queue `{key}`.",
                parse_mode=ParseMode.MARKDOWN
            )

        # load defs & compute ETA
        defs  = get_build_defs()
        info  = defs.get(key, {})
        delay = info.get("time_sec", 0)
        to_lvl = info and format_hhmmss(delay)

        # send initial building message with ETA
        name = info.get("name", key)
        eta  = format_hhmmss(delay)
        msg = await update.message.reply_text(
            f"🌱 Building *{name}* → Lvl {get_available_builds(uid)[-1]['level']+1} (ETA {eta})",
            parse_mode=ParseMode.MARKDOWN
        )

        # schedule the one-off completion
        context.job_queue.run_once(
            _complete_single_build,
            delay,
            data={"user_id": uid, "key": key},
            name=f"build_{uid}_{key}"
        )

        return

    # ── cancel a queued build ─────────────────────────────────────────────────
    if args and args[0].lower() == "cancel":
        if len(args) < 2:
            return await update.message.reply_text(
                f"Usage: {code('/build cancel <key>')}",
                parse_mode=ParseMode.MARKDOWN
            )
        key = args[1]
        ok  = cancel_build(uid, key)
        # remove scheduled job
        for job in context.job_queue.get_jobs_by_name(f"build_{uid}_{key}"):
            job.schedule_removal()

        return await update.message.reply_text(
            ("✅" if ok else "❌")
            + (f" Cancelled `{key}`." if ok else f" Failed to cancel `{key}`."),
            parse_mode=ParseMode.MARKDOWN
        )

    # ── list pending builds ────────────────────────────────────────────────────
    if args and args[0].lower() == "queue":
        q = get_build_queue(uid)
        if not q:
            return await update.message.reply_text("📭 Your build queue is empty.")
        defs   = {b["key"]: b for b in get_available_builds(uid)}
        now    = time.time()
        lines  = [section_header("⏳ Your Build Queue"), ""]
        buttons = []
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
            "\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=markup
        )

    # ── default: list all builds ───────────────────────────────────────────────
    allb = get_available_builds(uid)
    lines = [section_header("🏗️ Available Buildings"), ""]
    for b in allb:
        status = (
            "✅ Done" if b["done"]
            else "🔒 Locked" if b["locked"]
            else "💰 Affordable" if b["affordable"]
            else "❌ Too Expensive"
        )
        costs = f"{b['cost_c']}💳 {b['cost_m']}⛏️ {b['cost_e']}⚡"
        lines.append(
            f"*{b['name']}* (`{b['key']}`) — Tier {b['tier']} — _{status}_\n"
            f"Cost: {costs} | Time: {format_hhmmss(b['time_sec'])}\n"
        )
    lines.extend([
        "Queue one with `/build start <key>`",
        "Or cancel with `/build cancel <key>`"
    ])
    return await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

async def build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    uid = str(update.effective_user.id)
    await q.answer()
    _, key = q.data.split(":", 1)
    ok = cancel_build(uid, key)
    # also remove the scheduled job
    for job in context.job_queue.get_jobs_by_name(f"build_{uid}_{key}"):
        job.schedule_removal()
    await q.answer(
        text=("✅" if ok else "❌") + (" Cancelled" if ok else " Failed"),
        show_alert=True
    )
    # refresh queue view
    context.args = ["queue"]
    await build(update, context)

handler          = CommandHandler("build", build)
callback_handler = CallbackQueryHandler(build_callback, pattern=r"^build_cancel:")
