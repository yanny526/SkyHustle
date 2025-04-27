#   core/resources.py
#   Defines functions for managing player resources (ore, credits, energy)

from core.player import Player

#   Constants (can be moved to a config file later)
ORE_PER_MINE = 20
CREDITS_PER_MINE = 10
ENERGY_COST_PER_ORE = 5


def calculate_mining_rewards(player: Player, amount: int) -> tuple[int, int]:
    """
    Calculates the ore and credits gained from mining.

    Args:
        player: The player mining.
        amount: The amount of ore to mine.

    Returns:
        A tuple containing (ore_gain, credits_gain).
    """
    ore_gain = ORE_PER_MINE * amount + (player.refinery_level * 5)
    credits_gain = CREDITS_PER_MINE * amount
    return ore_gain, credits_gain


def calculate_mining_cost(amount: int) -> int:
    """
    Calculates the energy cost of mining.

    Args:
        amount: The amount of ore to mine.

    Returns:
        The energy cost.
    """
    return ENERGY_COST_PER_ORE * amount


def apply_mining_results(player: Player, ore_gain: int, credits_gain: int, energy_cost: int):
    """
    Applies the results of mining to the player's resources.

    Args:
        player: The player who mined.
        ore_gain: The ore gained from mining.
        credits_gain: The credits gained from mining.
        energy_cost: The energy cost of mining.
    """
    player.ore += ore_gain
    player.credits += credits_gain
    player.energy -= energy_cost


def reset_daily_resources(player: Player):
    """
    Resets daily resources (if any) for the player.
    (Currently a placeholder - might not be needed)
    """
    #   Placeholder for future daily resource resets (if applicable)
    pass
