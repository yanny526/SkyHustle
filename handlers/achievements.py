# handlers/achievements.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from modules.achievement_manager import load_achievements, get_player_achievement
from utils.format_utils import section_header

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /achievements – show your achievements and completion status.
    """
    uid  = str(update.effective_user.id)
    args = context.args

    # ─── Help Screen ─────────────────────────────────────────────────────────
    if args and args[0].lower() == "help":
        lines = [
            section_header("🏅 Achievements Help 🏅", pad_char="=", pad_count=3),
            "",
            "Track your milestones and earn rewards as you progress.",
            "",
            section_header("📜 View Achievements", pad_char="-", pad_count=3),
            "`/achievements`",
            "→ List all achievements and see which you’ve unlocked.",
            "",
            section_header("🎁 Claim Rewards", pad_char="-", pad_count=3),
            "Rewards are automatically granted upon completion.",
            "",
            "Keep an eye on `/status` for updated resource totals."
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # ─── Load & Partition Achievements ────────────────────────────────────────
    all_achs = load_achievements()
    done     = []
    pending  = []
    for ach in all_achs:
        idx, prow = get_player_achievement(uid, ach.id)
        if prow and prow[3]:  # prow[3] indicates completion
            done.append(ach.description)
        else:
            pending.append(ach.description)

    # ─── Build UI ──────────────────────────────────────────────────────────────
    lines = [
        section_header("🏅 Your Achievements", pad_char="=", pad_count=3),
        ""
    ]
    if done:
        lines.append("✅ *Unlocked*")
        for desc in done:
            lines.append(f" • {desc}")
        lines.append("")
    if pending:
        lines.append("❌ *Locked*")
        for desc in pending:
            lines.append(f" • {desc}")
        lines.append("")
    lines.append("Type `/achievements help` for usage info.")

    # ─── Inline Refresh Button ────────────────────────────────────────────────
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔄 Refresh", callback_data="achievements")
    )

    text = "\n".join(lines)
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def achievements_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "achievements":
        return await achievements(update, context)

handler          = CommandHandler("achievements", achievements)
callback_handler = CallbackQueryHandler(achievements_button, pattern="^achievements$")
