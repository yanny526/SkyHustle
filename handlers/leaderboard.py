from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from sheets_service import get_rows

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard
    Fetches the top 10 players by score from the 'Leaderboard' sheet.
    """
    # read all rows (skip header)
    rows = get_rows("Leaderboard")[1:]
    if not rows:
        await update.message.reply_text("🏆 Leaderboard is empty—no scores yet.")
        return

    # sort descending by score (3rd column)
    try:
        sorted_rows = sorted(
            rows,
            key=lambda r: int(r[2]),
            reverse=True
        )
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Error parsing leaderboard data.")
        return

    # build a message
    text = "🏆 *Leaderboard* 🏆\n\n"
    for i, row in enumerate(sorted_rows[:10], start=1):
        username = row[1]
        score    = row[2]
        text += f"{i}. {username} — {score}\n"

    await update.message.reply_markdown(text)

handler = CommandHandler("leaderboard", leaderboard)
