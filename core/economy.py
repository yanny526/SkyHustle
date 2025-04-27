#   core/economy.py
#   Defines functions for Black Market transactions and item effects

from core.player import Player

#   Constants (can be moved to a config file later, or loaded from JSON)
BLACK_MARKET_ITEMS = {
    "infinityscout": {"description": "Gain 5 scouts", "price": 100},
    "reviveall": {"description": "Revive 5 of each unit", "price": 200},
    "hazmat": {"description": "Increase ore mining", "price": 150},
}


def black_market_price(item_id: str) -> int:
    """
    Returns the price of a Black Market item.

    Args:
        item_id: The ID of the item.

    Returns:
        The price of the item, or 0 if the item is not found.
    """
    item = BLACK_MARKET_ITEMS.get(item_id)
    if item:
        return item["price"]
    return 0


def apply_item_effects(player: Player, item_id: str):
    """
    Applies the effects of a purchased item to the player.

    Args:
        player: The player who purchased the item.
        item_id: The ID of the item.

    This is where you'd implement the actual effects of the items.
    For now, it's a placeholder.
    """

    if item_id == "infinityscout":
        player.army["scout"] += 5
    elif item_id == "reviveall":
        for unit in player.army:
            player.army[unit] += 5
    elif item_id == "hazmat":
        player.refinery_level += 1
    # Add more item effects here
    player.items.append(item_id)  # Add item to player's inventory
