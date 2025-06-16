# handlers/leaderboard.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from utils.decorators import game_command
from utils.format_utils import section_header
from sheets_service import get_rows, update_row
from modules.unit_manager import UNITS  # dynamic unit power lookup

@game_command
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard – show top commanders by power (and auto-reward Top 3).
    Also handles callback queries for “Refresh” and “Help”.
    """
    # if this came from a button, clear the “loading” state
    if update.callback_query:
        await update.callback_query.answer()

    args = context.args or []

    # ─── Help Screen ─────────────────────────────────────────────────────────
    if args and args[0].lower() == "help":
        lines = [
            section_header("🏆 Leaderboard Help 🏆", pad_char="=", pad_count=3),
            "",
            "View the ranking of top commanders by combined base & army power.",
            "",
            section_header("📜 Usage", pad_char="-", pad_count=3),
            "`/leaderboard`",
            "→ Show the top 10 commanders.",
            "",
            "🏅 Top 3 Placement",
            "Rewards are automatically granted when you enter the Top 3 for the first time.",
            "",
            "Use `/leaderboard` anytime to refresh this list."
        ]
        text = "\n".join(lines)
        kb = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("🔄 Back to Leaderboard", callback_data="leaderboard")
        )
        if update.message:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        else:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return

    # ─── Compute Scores ───────────────────────────────────────────────────────
    players_sheet = get_rows('Players')
    header = players_sheet[0]
    data = players_sheet[1:]

    # Building power
    build_rows = get_rows('Buildings')[1:]
    build_power = {}
    for uid, _, lvl, *_ in build_rows:
        try:
            build_power[uid] = build_power.get(uid, 0) + int(lvl)
        except ValueError:
            pass

    # Army power
    army_rows = get_rows('Army')[1:]
    army_power = {}
    for uid, unit_key, cnt_str in army_rows:
        if unit_key in UNITS:
            power = UNITS[unit_key][3]
            try:
                army_power[uid] = army_power.get(uid, 0) + int(cnt_str) * power
            except ValueError:
                pass

    # Combine and sort
    scores = []
    for uid, name, *rest in data:
        total = build_power.get(uid, 0) + army_power.get(uid, 0)
        scores.append((uid, name or "Unknown", total))
    scores.sort(key=lambda x: x[2], reverse=True)

    # ─── Reward Top 3 ────────────────────────────────────────────────────────
    badge_idx = next((i for i, col in enumerate(header) if col.lower() == 'badge'), None)
    credit_reward, mineral_reward = 2000, 1000
    badge_text = "🏅 Top 3 Commander"

    for pos, (uid, name, _) in enumerate(scores[:3], start=1):
        for ridx, prow in enumerate(players_sheet[1:], start=1):
            if prow[0] != uid:
                continue
            # extend row if needed
            while len(prow) < len(header):
                prow.append("")
            if badge_idx is not None and prow[badge_idx] != badge_text:
                prow[3] = str(int(prow[3]) + credit_reward)
                prow[4] = str(int(prow[4]) + mineral_reward)
                prow[badge_idx] = badge_text
                update_row('Players', ridx, prow)
                congrats = (
                    f"🎉 Commander *{name}* reached *Top {pos}*! 🎉\n"
                    f"Rewards: +{credit_reward}💳 +{mineral_reward}⛏️"
                )
                if update.message:
                    await update.message.reply_text(congrats, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.callback_query.bot.send_message(
                        update.effective_chat.id, congrats, parse_mode=ParseMode.MARKDOWN
                    )
            break

    # ─── Build Leaderboard UI ────────────────────────────────────────────────
    lines = [section_header("🏆 Leaderboard", pad_char="=", pad_count=3), ""]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for idx, (_, name, power) in enumerate(scores[:10], start=1):
        prefix = medals.get(idx, f"{idx}.")
        lines.append(f"{prefix} *{name}* — {power} Power")
    lines.append("")
    lines.append("Type `/leaderboard help` for usage info.")

    text = "\n".join(lines)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="leaderboard")],
        [InlineKeyboardButton("❓ Help",    callback_data="leaderboard_help")],
    ])

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def leaderboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle both “leaderboard” (refresh) and “leaderboard_help” callbacks.
    """
    data = update.callback_query.data
    # map callback to args so /leaderboard help runs
    if data == "leaderboard_help":
        context.args = ["help"]
    else:
        context.args = []
    return await leaderboard(update, context)


# Register both the command and its callbacks
handler          = CommandHandler('leaderboard', leaderboard)
callback_handler = CallbackQueryHandler(leaderboard_button, pattern=r"^leaderboard(_help)?$")
