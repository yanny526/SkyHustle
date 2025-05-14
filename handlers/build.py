import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.building_manager import (
    get_available_builds,
    start_build,
    get_build_queue,
    cancel_build,
)
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header, code

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build                    → list all buildings (locked/affordable/done)
    /build start <key>        → queue an upgrade
    /build queue              → view pending upgrades
    /build cancel <key>       → cancel a queued upgrade
    """
    uid = str(update.effective_user.id)
    args = context.args or []

    # start
    if args and args[0].lower()=="start":
        if len(args)<2:
            return await update.message.reply_text(f"Usage: {code('/build start <key>')}", parse_mode=ParseMode.MARKDOWN)
        ok = start_build(uid, args[1])
        return await update.message.reply_text(
            ("✅" if ok else "❌") + (f" Build `{args[1]}` queued." if ok else f" Cannot queue `{args[1]}`."),
            parse_mode=ParseMode.MARKDOWN
        )

    # cancel
    if args and args[0].lower()=="cancel":
        if len(args)<2:
            return await update.message.reply_text(f"Usage: {code('/build cancel <key>')}", parse_mode=ParseMode.MARKDOWN)
        ok = cancel_build(uid, args[1])
        return await update.message.reply_text(
            ("✅" if ok else "❌") + (f" Cancelled `{args[1]}`." if ok else f" Failed to cancel `{args[1]}`."),
            parse_mode=ParseMode.MARKDOWN
        )

    # queue
    if args and args[0].lower()=="queue":
        q = get_build_queue(uid)
        if not q:
            return await update.message.reply_text("📭 Your build queue is empty.")
        defs = {b["key"]:b for b in get_available_builds(uid)}
        now = time.time()
        lines = [section_header("⏳ Your Build Queue"), ""]
        buttons = []
        for item in q:
            info = defs.get(item["key"],{})
            name = info.get("name", item["key"])
            left = max(0,int(item["end_ts"]-now))
            lines.append(f"*{name}* — {format_hhmmss(left)} left")
            buttons.append([InlineKeyboardButton(f"❌ Cancel {name}", callback_data=f"build_cancel:{item['key']}")])
        markup=InlineKeyboardMarkup(buttons)
        return await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    # default list all
    allb = get_available_builds(uid)
    lines = [section_header("🏗️ Available Buildings"), ""]
    for b in allb:
        key,name,tier = b["key"],b["name"],b["tier"]
        status = ("✅ Done" if b["done"] else 
                  "🔒 Locked" if b["locked"] else
                  "💰 Affordable" if b["affordable"] else
                  "❌ Too Expensive")
        costs = f"{b['cost_c']}💳 {b['cost_m']}⛏️ {b['cost_e']}⚡"
        lines.append(f"*{name}* (`{key}`) — Tier {tier} — _{status}_\nCost: {costs} | Time: {format_hhmmss(b['time_sec'])}\n")
    lines.append("Queue one with `/build start <key>`")
    lines.append("Or cancel with `/build cancel <key>`")
    return await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

async def build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _,key = q.data.split(":",1)
    ok = cancel_build(str(update.effective_user.id), key)
    await q.answer(text=("✅" if ok else "❌")+" Cancelled" if ok else "Failed", show_alert=True)
    # refresh
    context.args=["queue"]
    await build(update, context)

handler          = CommandHandler("build", build)
callback_handler = CallbackQueryHandler(build_callback, pattern=r"^build_cancel:")
