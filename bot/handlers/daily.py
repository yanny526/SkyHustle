# handlers/daily.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta

from utils.format import section_header

daily_rewards = [
    {"credits": 500, "minerals": 200, "energy": 100},
    {"credits": 300, "minerals": 150, "energy": 80},
    {"credits": 400, "minerals": 250, "energy": 90},
    {"credits": 350, "minerals": 220, "energy": 75},
    {"credits": 500, "minerals": 300, "energy": 120},
    {"credits": 600, "minerals": 350, "energy": 150},
    {"credits": 700, "minerals": 400, "energy": 200},
]

current_event = {
    "name": "Resource Rush",
    "description": "Double mineral production for all players!",
    "start": datetime.now() - timedelta(days=1),
    "end": datetime.now() + timedelta(days=3),
    "active": True
}

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = datetime.now()

    # Check if event is active
    if current_event["active"] and now >= current_event["start"] and now <= current_event["end"]:
        event_info = (
            f"{section_header('ACTIVE EVENT', '🎉', 'magenta')}\n\n"
            f"**{current_event['name']}**\n"
            f"{current_event['description']}\n\n"
            f"Started: {current_event['start'].strftime('%Y-%m-%d %H:%M')}\n"
            f"Ends: {current_event['end'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    else:
        event_info = "No active events at this time.\n\n"

    # Check daily login reward
    players = get_rows("Players")
    last_login = None
    for row in players[1:]:
        if row[0] == uid:
            if len(row) > 8 and row[8]:
                last_login = datetime.fromtimestamp(int(row[8]))
            break

    if not last_login or (now.date() - last_login.date()).days >= 1:
        # Calculate daily reward index (0-6 based on day of week)
        reward_index = now.weekday()
        reward = daily_rewards[reward_index]

        # Update player resources
        update_player_resources(uid, reward["credits"], reward["minerals"], reward["energy"])

        await update.message.reply_text(
            f"{section_header('DAILY REWARDS', '📅', 'cyan')}\n\n"
            f"Here's your daily login bonus!\n"
            f"Credits: +{reward['credits']}💰\n"
            f"Minerals: +{reward['minerals']}⛏️\n"
            f"Energy: +{reward['energy']}⚡\n\n" +
            event_info +
            "Use /daily to claim your rewards!\n"
            "Use /events to see current events!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"{section_header('DAILY REWARDS', '📅', 'cyan')}\n\n"
            f"You've already claimed today's rewards!\n"
            f"Come back tomorrow for more!\n\n" +
            event_info +
            "Use /events to see current events!",
            parse_mode="Markdown"
        )
