#   handlers/army.py
#   Handles army-related commands: ,forge and ,use

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from core import player  #   Import player-related functions
from core import army  #   Import army-related functions

async def forge_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]
):
    """
    Handles the ,forge <unit> <count> command.

    Creates new army units if the player has sufficient resources.
    Validates input and updates the player's army.
    """

    if len(args) != 2:
        await update.message.reply_text(
            "⚠️ Incorrect command format. Usage: `,forge <unit> <count>`"
        )
        return

    unit = args[0].lower()
    try:
        count = int(args[1])
        if count <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid count. Please specify a positive whole number."
        )
        return

    if unit not in ["scout", "tank", "drone"]:
        await update.message.reply_text(
            "⚠️ Invalid unit type. Available units: scout, tank, drone."
        )
        return

    current_player = player.find_or_create_player(update.message.chat_id)
    cost_ore, cost_credits = army.calculate_unit_cost(unit, count)

    if current_player.ore < cost_ore or current_player.credits < cost_credits:
        await update.message.reply_text(
            "💰 Insufficient resources. You need more ore and/or credits."
        )
        return

    current_player.ore -= cost_ore
    current_player.credits -= cost_credits
    army.add_units_to_army(current_player, unit, count)
    player.save_player(current_player)

    await update.message.reply_text(
        f"🏭 {count} {unit}(s) forged! You spent {cost_ore} ore and {cost_credits} credits.",
        parse_mode=ParseMode.MARKDOWN,
    )

async def use_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]
):
    """
    Handles the ,use <item> command.

    Uses a specified item from the player's inventory.
    This is a placeholder for item effects; the logic will be expanded later.
    """

    if not args:
        await update.message.reply_text(
            "⚠️ Incorrect command format. Usage: `,use <item>`"
        )
        return

    item_id = args[0].lower()
    current_player = player.find_or_create_player(update.message.chat_id)

    if item_id not in current_player.items:
        await update.message.reply_text("📦 You do not possess this item.")
        return

    # Placeholder for item effects
    # In the future, this is where you'd call functions to apply item effects
    # based on the item_id.
    await update.message.reply_text(
        f"✨ You have used the {item_id}. Its effects have been applied.",
        parse_mode=ParseMode.MARKDOWN,
    )
