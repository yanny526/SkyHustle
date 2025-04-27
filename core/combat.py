#   core/combat.py
#   Defines functions for handling combat between players

from core.player import Player
import random

# Constants (can be moved to a config file later)
BASE_ATTACK = 5
BASE_DEFENSE = 5
UNIT_STATS = {
    "scout": {"attack": 1, "defense": 1, "speed": 3},
    "tank": {"attack": 3, "defense": 5, "speed": 1},
    "drone": {"attack": 2, "defense": 2, "speed": 4},
}


def calculate_attack_damage(attacker: Player, defender: Player) -> int:
    """
    Calculates the damage an attacker inflicts on a defender.

    This is a simplified combat calculation. A more complex system
    might consider unit types, levels, upgrades, and random factors.

    Args:
        attacker: The player initiating the attack.
        defender: The player being attacked.

    Returns:
        The amount of damage inflicted (can be positive or negative).
        Positive damage means attacker wins, negative means defender wins
    """

    attacker_attack = BASE_ATTACK
    defender_defense = BASE_DEFENSE

    for unit, count in attacker.army.items():
        attacker_attack += UNIT_STATS.get(unit, {}).get("attack", 0) * count

    for unit, count in defender.army.items():
        defender_defense += UNIT_STATS.get(unit, {}).get("defense", 0) * count

    damage = attacker_attack - defender_defense + random.randint(
        -5, 5
    )  # Add some randomness
    return damage


def apply_attack_results(attacker: Player, defender: Player, damage: int):
    """
    Applies the results of an attack to both players.

    This might involve reducing army units, resources, or other effects
    depending on the game mechanics. For now, it's a placeholder.

    Args:
        attacker: The attacking player.
        defender: The defending player.
        damage: The damage calculated in calculate_attack_damage().
    """
    # Placeholder for applying attack results
    # For a more detailed system, you might:
    # - Reduce army units based on damage
    # - Affect player resources
    # - Apply status effects

    # Simplified result:
    if damage > 0:
        # Attacker wins (for now, just a message is sent)
        pass
    else:
        # Defender wins
        pass
