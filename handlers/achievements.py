from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from modules.achievement_manager import load_achievements, get_player_achievement

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    all_achs = load_achievements()
    lines = ["🏅 *Your Achievements*",""]
    for a in all_achs:
        idx, prow = get_player_achievement(uid, a.id)
        status = "✅" if prow else "❌"
        lines.append(f"{status} {a.description}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

handler = CommandHandler('achievements', achievements)
