#   core/army.py
#   Defines functions for managing army units (scouts, tanks, drones)

from core.player import Player
from typing import Tuple, Dict

#   Constants (can be moved to a config file later)
UNIT_COSTS = {
    "scout": {"ore": 10, "credits": 5},
    "tank": {"ore": 20, "credits": 15},
    "drone": {"ore": 15, "credits": 10},
}


def calculate_unit_cost(unit: str, count: int) -> Tuple[int, int]:
    """
    Calculates the total ore and credit cost of forging units.

    Args:
        unit: The type of unit being forged ("scout", "tank", "drone").
        count: The number of units being forged.

    Returns:
        A tuple containing (total_ore_cost, total_credit_cost).
    """

    if unit not in UNIT_COSTS:
        return 0, 0  #   Invalid unit

    ore_cost = UNIT_COSTS[unit]["ore"] * count
    credit_cost = UNIT_COSTS[unit]["credits"] * count
    return ore_cost, credit_cost


def add_units_to_army(player: Player, unit: str, count: int):
    """
    Adds units to the player's army.

    Args:
        player: The player whose army is being updated.
        unit: The type of unit being added.
        count: The number of units being added.
    """

    if unit not in player.army:
        player.army[unit] = 0  #   Initialize if unit type doesn't exist
    player.army[unit] += count


def remove_units_from_army(player: Player, unit: str, count: int):
    """
    Removes units from the player's army.

    Args:
        player: The player whose army is being updated.
        unit: The type of unit being removed.
        count: The number of units being removed.
    """

    if unit not in player.army:
        return  #   Player doesn't have this unit type

    player.army[unit] -= count
    if player.army[unit] < 0:
        player.army[unit] = 0  #   Ensure count doesn't go below zero


def get_army_strength(player: Player) -> int:
    """
    Calculates the total strength of the player's army (placeholder).

    This is a placeholder for a more complex calculation that might
    consider unit types, levels, etc. For now, it just returns the
    total number of units.

    Args:
        player: The player whose army strength is being calculated.

    Returns:
        The total army strength.
    """
    total_strength = sum(player.army.values())
    return total_strength


def get_unit_stats(unit: str) -> Dict[str, int]:
    """
    Returns the stats of a given unit type (placeholder).

    This is a placeholder for a more complex system where units have
    different attack, defense, speed, etc.
    """
    # Placeholder for unit stats
    unit_stats = {
        "scout": {"attack": 1, "defense": 1, "speed": 3},
        "tank": {"attack": 3, "defense": 5, "speed": 1},
        "drone": {"attack": 2, "defense": 2, "speed": 4},
    }
    return unit_stats.get(unit, {})
