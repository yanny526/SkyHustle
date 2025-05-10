# handlers/achievements.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.achievements import Achievement
from utils.format import section_header

achievements_data = [
    Achievement("First Victory", "Win your first battle", 100),
    Achievement("Base Builder", "Upgrade a building to level 5", 200),
    Achievement("Army Commander", "Train 100 units", 300),
    Achievement("Resource Master", "Gather 10,000 credits", 500),
]

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    if not args:
        kb = [[InlineKeyboardButton(f"{ach.name} - {'✅' if ach.unlocked else '❌'}", callback_data=f"achievement_{i}")] for i, ach in enumerate(achievements_data)]
        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('ACHIEVEMENTS', '🏅', 'silver')}\n\n"
            "Complete challenges to earn rewards:\n\n" +
            "\n".join([f"{i+1}. {ach.name}: {ach.description} - Reward: {ach.reward} credits" for i, ach in enumerate(achievements_data)]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    achievement_id = args[0]
    if achievement_id.isdigit() and 0 <= int(achievement_id) < len(achievements_data):
        achievement = achievements_data[int(achievement_id)]
        if not achievement.unlocked:
            achievement.unlock()
            await update.message.reply_text(
                f"✓ *Achievement Unlocked!* ✓\n\n"
                f"**{achievement.name}**\n"
                f"{achievement.description}\n"
                f"Reward: {achievement.reward} credits added!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✓ *Already Unlocked* ✓\n\n"
                f"**{achievement.name}**\n"
                f"{achievement.description}",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "Invalid achievement ID. Use /achievements to see available achievements.",
            parse_mode="Markdown"
        )
