#   handlers/resource.py
#   Handles resource-related commands: ,daily, ,mine, and ,missions

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import date, datetime, timedelta
from core import player  #   Import player-related functions


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,daily command.

    Claims the player's daily reward of resources.
    Prevents claiming multiple times per day.
    """

    current_player = player.find_or_create_player(update.message.chat_id)
    today = date.today()

    if current_player.last_daily == str(today):
        await update.message.reply_text(
            "🎁 Commander, you've already claimed your daily bonus today. Return tomorrow for more riches!"
        )
        return

    last_daily = datetime.strptime(
        current_player.last_daily, "%Y-%m-%d"
    ).date() if current_player.last_daily else None
    current_player.credits += 50
    current_player.energy += 20
    current_player.daily_streak = (
        current_player.daily_streak + 1 if last_daily == today - timedelta(days=1) else 1
    )  #   Increment streak if claimed yesterday
    current_player.last_daily = str(today)
    player.save_player(current_player)

    await update.message.reply_text(
        f"🎉 Daily Resources Claimed! +50 Credits, +20 Energy. Current Streak: {current_player.daily_streak} days",
        parse_mode=ParseMode.MARKDOWN,
    )


async def mine_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]
):
    """
    Handles the ,mine ore <amount> command.

    Mines ore, consuming energy.
    Validates input and checks for sufficient energy.
    """

    if len(args) != 2 or args[0] != "ore":
        await update.message.reply_text(
            "⚠️ Incorrect command format. Usage: `,mine ore <amount>`"
        )
        return

    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid amount. Please specify a positive whole number."
        )
        return

    current_player = player.find_or_create_player(update.message.chat_id)
    energy_cost = amount * 5

    if current_player.energy < energy_cost:
        await update.message.reply_text(
            "⚡ Insufficient energy. Mining requires 5 energy per unit of ore."
        )
        return

    ore_gain = 20 * amount + (current_player.refinery_level * 5)
    credits_gain = 10 * amount
    current_player.ore += ore_gain
    current_player.credits += credits_gain
    current_player.energy -= energy_cost
    player.save_player(current_player)

    await update.message.reply_text(
        f"⛏️ Mining successful! You've extracted {ore_gain} ore and earned {credits_gain} credits.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def missions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,missions command.

    Displays the player's current daily missions and their progress.
    """

    current_player = player.find_or_create_player(update.message.chat_id)
    today = date.today()

    if current_player.last_mission_reset != str(today):
        #   Missions reset daily
        current_player.missions = {
            "mine5": False,
            "win1": False,
            "forge5": False,
        }
        current_player.last_mission_reset = str(today)
        player.save_player(current_player)

    missions_message = "📜 *Daily Missions:* 📜\n\n"
    missions_message += (
        f"- Mine 5 Ore: {'✅' if current_player.missions.get('mine5') else '⬜'}\n"
    )
    missions_message += (
        f"- Win 1 Battle: {'✅' if current_player.missions.get('win1') else '⬜'}\n"
    )
    missions_message += (
        f"- Forge 5 Units: {'✅' if current_player.missions.get('forge5') else '⬜'}\n"
    )

    missions_message += "\nComplete missions to earn extra rewards!"
    await update.message.reply_text(missions_message, parse_mode=ParseMode.MARKDOWN)
