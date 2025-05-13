
# handlers/build.py

import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import get_rows, append_row, update_row
from utils.time_utils import format_hhmmss
from utils.decorators import game_command
from config import BUILDING_MAX_LEVEL
from utils.format_utils import (
    get_build_time,
    get_build_costs,
    get_building_emoji,
    section_header,
)

BUILDINGS = {
    'mine': ('Mine', '⛏️'),
    'powerplant': ('Power Plant', '⚡'),
    'power plant': ('Power Plant', '⚡'),
    'barracks': ('Barracks', '🛡️'),
    'workshop': ('Workshop', '🔧'),
}

@game_command
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_user.id)
    args = context.args.copy()

    # ─── Help Screen ─────────────────────────────────────────────────────────
    if not args or args[0].lower() == "help":
        lines = [
            section_header("🏗️ BUILDING CONSTRUCTION 🏗️", pad_char="=", pad_count=3),
            "",
            "Expand your empire by upgrading structures:",
            "",
            section_header("⛏️ Upgrade Your Mine", pad_char="-", pad_count=3),
            "`/build mine`",
            "→ Increase mineral output each minute.",
            "",
            section_header("⚡ Upgrade Power Plant", pad_char="-", pad_count=3),
            "`/build powerplant`",
            "→ Boost your energy generation.",
            "",
            section_header("🛡️ Upgrade Barracks", pad_char="-", pad_count=3),
            "`/build barracks`",
            "→ Train military units faster.",
            "",
            section_header("🔧 Upgrade Workshop", pad_char="-", pad_count=3),
            "`/build workshop`",
            "→ Unlock advanced unit types.",
            "",
            "Valid buildings: mine, powerplant, barracks, workshop",
            "Check `/queue` to view active upgrades."
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Validate Choice ──────────────────────────────────────────────────────
    key = args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"❌ Unknown building *{args[0]}*.",
            parse_mode=ParseMode.MARKDOWN
        )
    btype, emoji = BUILDINGS[key]

    # ─── Current Level & Cap Check ─────────────────────────────────────────────
    current_lvl = 0
    buildings = get_rows("Buildings")
    for row in buildings[1:]:
        if row[0] == uid and row[1] == btype:
            current_lvl = int(row[2] or 0)
            break

    max_lvl = BUILDING_MAX_LEVEL.get(btype)
    if max_lvl is not None and current_lvl >= max_lvl:
        return await update.message.reply_text(
            f"🏆 *{btype}* is already max Level {max_lvl}!",
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Compute Next Level, Costs & Time ──────────────────────────────────────
    next_lvl = current_lvl + 1
    costC, costM, costE = get_build_costs(btype, next_lvl)
    duration = get_build_time(btype, next_lvl)

    # ─── Check Resources & Capture Tutorial Progress ───────────────────────────
    players = get_rows("Players")
    header = players[0]
    progress_idx = header.index("progress") if "progress" in header else None
    old_progress = None

    for pi, prow in enumerate(players[1:], start=1):
        if prow[0] == uid:
            try:
                credits, minerals, energy = map(int, (prow[3], prow[4], prow[5]))
            except Exception:
                return await update.message.reply_text(
                    "❗ Run /start first.",
                    parse_mode=ParseMode.MARKDOWN
                )
            # record old tutorial progress
            if progress_idx is not None and len(prow) > progress_idx:
                old_progress = prow[progress_idx]
            break
    else:
        return await update.message.reply_text(
            "❗ Run /start first.",
            parse_mode=ParseMode.MARKDOWN
        )

    if credits < costC or minerals < costM or energy < costE:
        return await update.message.reply_text(
            f"❌ Need {costC}💳 {costM}⛏️ {costE}⚡.",
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Deduct & Schedule Upgrade ─────────────────────────────────────────────
    players[pi][3] = str(credits - costC)
    players[pi][4] = str(minerals - costM)
    players[pi][5] = str(energy - costE)
    update_row("Players", pi, players[pi])

    end_ts = time.time() + duration
    existing = next(
        ((bi, brow) for bi, brow in enumerate(buildings[1:], start=1)
         if brow[0] == uid and brow[1] == btype),
        None
    )
    if existing:
        bi, brow = existing
        new_row = brow.copy()
        while len(new_row) < 4:
            new_row.append("")
        new_row[3] = str(end_ts)
        update_row("Buildings", bi, new_row)
    else:
        append_row("Buildings", [uid, btype, str(current_lvl), str(end_ts)])

    # ─── Tutorial Progression Step 2 ➔ 3 ───────────────────────────────────────
    if btype == "Power Plant" and old_progress == "2":
        # advance tutorial progress to step 3
        if progress_idx is not None:
            players[pi][progress_idx] = "3"
            update_row("Players", pi, players[pi])

        lines = [
            section_header("✅ Power Plant Constructed!", pad_char="=", pad_count=3),
            "",
            f"{emoji} *{btype}* now at Level *{next_lvl}*",
            "",
            section_header("🧾 Tutorial Step 3", pad_char="-", pad_count=3),
            "`/train soldier` — Prepare your first unit for battle.",
        ]
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("/train soldier")], [KeyboardButton("/status")]],
            resize_keyboard=True
        )
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )

    # ─── Confirmation UI ───────────────────────────────────────────────────────
    lines = [
        section_header(f"🔨 Upgrading {btype} → Level {next_lvl}", pad_char="-", pad_count=3),
        "",
        f"{emoji} *{btype}* now at Level *{next_lvl}*",
        f"Cost: {costC}💳 {costM}⛏️ {costE}⚡",
        f"Duration: {format_hhmmss(duration)}",
    ]
    kb = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("⏳ View Queue", callback_data="queue"),
        InlineKeyboardButton("📊 Check Status", callback_data="status"),
    ])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

handler = CommandHandler("build", build)
