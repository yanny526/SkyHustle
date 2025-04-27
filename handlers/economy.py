#   handlers/economy.py
#   Handles economy-related commands: ,unlockbm, ,blackmarket, and ,buy

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from core import player  #   Import player-related functions
from core import economy  #   Import economy-related functions

# Constants for Black Market unlock cost
UNLOCK_BM_COST = 200


async def unlockbm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,unlockbm command.

    Unlocks the Black Market for the player if they have sufficient credits.
    """

    current_player = player.find_or_create_player(update.message.chat_id)

    if current_player.black_market_unlocked:
        await update.message.reply_text(
            "🔓 Commander, the Black Market is already accessible."
        )
        return

    if current_player.credits < UNLOCK_BM_COST:
        await update.message.reply_text(
            f"💰 Insufficient credits. Unlocking the Black Market requires {UNLOCK_BM_COST} credits."
        )
        return

    current_player.credits -= UNLOCK_BM_COST
    current_player.black_market_unlocked = True
    player.save_player(current_player)

    await update.message.reply_text(
        "🔓 Black Market unlocked! New opportunities await...",
        parse_mode=ParseMode.MARKDOWN,
    )


async def blackmarket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,blackmarket command.

    Displays the items currently available in the Black Market.
    """

    current_player = player.find_or_create_player(update.message.chat_id)

    if not current_player.black_market_unlocked:
        await update.message.reply_text(
            "🔒 The Black Market remains hidden. Unlock it with `,unlockbm` first."
        )
        return

    # Placeholder for Black Market items (replace with actual data)
    black_market_items = {
        "infinityscout": "Gain 5 scouts",
        "reviveall": "Revive 5 of each unit",
        "hazmat": "Increase ore mining",
    }

    black_market_message = "⚫ *Black Market Emporium* ⚫\n\n"
    for item, description in black_market_items.items():
        price = economy.black_market_price(item)
        black_market_message += f"- {item}: {description} ({price} credits)\n"

    black_market_message += "\nUse `,buy <item>` to acquire these exclusive goods."
    await update.message.reply_text(black_market_message, parse_mode=ParseMode.MARKDOWN)


async def buy_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]
):
    """
    Handles the ,buy <item> command.

    Purchases an item from the Black Market if the player has sufficient credits.
    Applies the item's effects.
    """

    if not args:
        await update.message.reply_text(
            "⚠️ Incorrect command format. Usage: `,buy <item>`"
        )
        return

    item_id = args[0].lower()
    current_player = player.find_or_create_player(update.message.chat_id)

    if not current_player.black_market_unlocked:
        await update.message.reply_text(
            "🔒 The Black Market remains inaccessible. Unlock it with `,unlockbm`."
        )
        return

    item_price = economy.black_market_price(item_id)
    if item_price == 0:
        await update.message.reply_text("❌ Item not found in the Black Market.")
        return

    if current_player.credits < item_price:
        await update.message.reply_text(
            "💰 Insufficient credits to purchase this item."
        )
        return

    current_player.credits -= item_price
    economy.apply_item_effects(current_player, item_id)  #   Apply item effects
    player.save_player(current_player)

    await update.message.reply_text(
        f"✅ {item_id} acquired! Its power is now yours.", parse_mode=ParseMode.MARKDOWN
    )
