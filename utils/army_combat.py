import json

# Load unit stats from config
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)


def calculate_battle_outcome(
    player_army: dict[str, int], target_army: dict[str, int]
) -> tuple[str, str]:
    """
    Calculates the outcome of a battle between two armies.

    Returns:
        outcome (str): "Victory", "Defeat", or "Draw"
        battle_log (str): summary of power and casualties
    """
    # Compute total attack power
    player_power = sum(
        UNIT_STATS.get(unit, {}).get("attack", 0) * count
        for unit, count in player_army.items()
    )
    target_power = sum(
        UNIT_STATS.get(unit, {}).get("attack", 0) * count
        for unit, count in target_army.items()
    )

    # Total units for casualty calculations
    total_player = sum(player_army.values())
    total_target = sum(target_army.values())

    # Casualties proportional to opponent power, avoid division by zero
    if player_power + target_power > 0:
        player_casualties = min(
            total_player,
            int(total_player * (target_power / (player_power + target_power)))
        )
        target_casualties = min(
            total_target,
            int(total_target * (player_power / (player_power + target_power)))
        )
    else:
        player_casualties = 0
        target_casualties = 0

    # Determine outcome
    if player_power > target_power:
        outcome = "Victory"
    elif player_power < target_power:
        outcome = "Defeat"
    else:
        outcome = "Draw"

    # Build battle log
    battle_log = (
        f"Your Power: {player_power}  |  Enemy Power: {target_power}\n"
        f"You lost {player_casualties} unit(s), Enemy lost {target_casualties} unit(s)."
    )

    return outcome, battle_log


def calculate_battle_rewards(
    outcome: str,
    player_army: dict[str, int],
    target_army: dict[str, int]
) -> str:
    """
    Determines resource rewards or penalties based on battle outcome.

    Returns:
        str: human-readable rewards description
    """
    if outcome == "Victory":
        # Flat rewards
        return "500 Metal, 300 Fuel, 50 Crystals"
    elif outcome == "Defeat":
        # Penalty description (actual deduction handled elsewhere)
        return "Penalty: 10% of your total resources lost."
    else:
        return "No rewards (Draw)."
