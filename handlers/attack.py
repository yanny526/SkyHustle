import time
import random
import json
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header
from modules.unit_manager import UNITS
from modules.challenge_manager import load_challenges, update_player_progress

# where we track troops in flight
DEPLOY_SHEET  = "DeployedArmy"
DEPLOY_HEADER = ["job_name","uid","unit_key","quantity"]

# where we track pending operations & their codes
PEND_SHEET    = "PendingActions"
PEND_HEADER   = [
    "job_name","code","uid","defender_id","defender_name",
    "composition","scout_count","run_time","type","status"
]

def _ensure_deploy_sheet():
    rows = get_rows(DEPLOY_SHEET)
    if not rows or rows[0] != DEPLOY_HEADER:
        append_row(DEPLOY_SHEET, DEPLOY_HEADER)

def _ensure_pending_sheet():
    rows = get_rows(PEND_SHEET)
    if not rows or rows[0] != PEND_HEADER:
        append_row(PEND_SHEET, PEND_HEADER)

@game_command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack                → show help & examples
    /attack <Commander> -u infantry:5 tanks:2        (standard attack)
    /attack <Commander> --scout-only -s 3           (recon only)
    /attack -c <CODE>                               (cancel mission)
    """
    uid      = str(update.effective_user.id)
    args     = context.args.copy()
    job_name = None
    code     = None

    # 0) Enhanced Help screen when no args or 'help'
    if not args or args[0].lower() == "help":
        lines = [
            section_header("🏰 COMMAND CENTER: Attack Protocols 🏰"),
            "",
            "Welcome, Commander! Issue your orders with confidence:",
            "",
            section_header("🗡️ Standard Assault", pad_char="=", pad_count=3),
            "`/attack EnemyCommander -u infantry:5 tanks:2`",
            "→ Launch a combined arms strike on EnemyCommander.",
            "",
            section_header("🔎 Reconnaissance Only", pad_char="=", pad_count=3),
            "`/attack EnemyCommander --scout-only -s 3`",
            "→ Send 3 scouts to gather intel.",
            "",
            section_header("❌ Abort Mission", pad_char="=", pad_count=3),
            "`/attack -c <CODE>`",
            "→ Cancel an en route mission by its command code.",
            "",
            "After dispatch, press **View Pending** below to track all active missions."
        ]
        kb = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("📜 View Pending", callback_data="reports")
        )
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )

    # 1) Cancellation?
    if "-c" in args:
        i = args.index("-c")
        try:
            code = args[i+1]
        except IndexError:
            return await update.message.reply_text(
                "❗ Usage to cancel: `/attack -c <CODE>`",
                parse_mode=ParseMode.MARKDOWN
            )

        _ensure_pending_sheet()
        pend = get_rows(PEND_SHEET)
        for idx, row in enumerate(pend[1:], start=1):
            job_name, prow_code, puid, *_rest = row
            if puid == uid and prow_code == code and row[9] == "pending":
                try:
                    context.job_queue.scheduler.remove_job(job_name)
                except Exception:
                    pass
                row[9] = "cancelled"
                update_row(PEND_SHEET, idx, row)
                # return troops logic omitted for brevity...
                return await update.message.reply_text(
                    f"🚫 Mission `{code}` cancelled. Troops are returning home.",
                    parse_mode=ParseMode.MARKDOWN
                )

        return await update.message.reply_text(
            f"❗ No pending mission found with code `{code}`.",
            parse_mode=ParseMode.MARKDOWN
        )

    # 2) Normal dispatch prep
    scout_only = "--scout-only" in args
    if scout_only:
        args.remove("--scout-only")

    target = args.pop(0)

    # Scouts
    scout_count = 0
    if "-s" in args:
        i = args.index("-s")
        if i+1 < len(args) and args[i+1].isdigit():
            scout_count = int(args[i+1])
        del args[i:i+2]

    # Custom composition
    comp = {}
    if "-u" in args:
        i = args.index("-u")
        raw = []
        for tok in args[i+1:]:
            if tok.startswith("-"):
                break
            raw.append(tok)
        del args[i:i+1+len(raw)]
        for pair in raw:
            if ":" in pair:
                k, v = pair.split(":", 1)
                if k in UNITS and v.isdigit():
                    comp[k] = int(v)

    # Default to full garrison if no composition and not scout-only
    if not comp and not scout_only:
        for r in get_rows("Army")[1:]:
            if r[0] == uid:
                comp[r[1]] = int(r[2])

    # --- remaining logic for locating players, checking energy,
    # scheduling jobs, scout/combat callbacks, etc. unchanged ---

    # Final UI Confirmation
    parts = [f"{UNITS[k][1]}×{v}" for k, v in comp.items()]
    if scout_count:
        parts.append(f"🔎 Scouts×{scout_count}")

    lines = [section_header("✅ Orders Received")]
    lines.append(f"🎯 Target: *{target}*")
    if scout_count:
        lines.append(f"🕒 Scouts arrive in {format_hhmmss(5*60)}")
    if job_name:
        lines.append(f"🕒 Assault lands in {format_hhmmss(30*60)}")
    lines.append("")
    lines.append(section_header("🗡️ Detachment"))
    lines.append("  " + "  ".join(parts))
    if job_name:
        lines.append("")
        lines.append(section_header("🏷️ Command Code"))
        lines.append(f"`{code}`  (cancel via `/attack -c {code}`)")

    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("📜 View Pending", callback_data="reports")
    )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("attack", attack)
