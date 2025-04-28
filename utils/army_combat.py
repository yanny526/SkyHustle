# army_combat.py

import json
import random
from datetime import datetime

# Load unit stats from config
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)

def calculate_battle_outcome(player_army, target_army):
    """
    Returns (outcome, battle_log)
    outcome: "Victory", "Defeat", or "Draw"
    battle_log: summary of power and casualties
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

    # Total units
    total_player_units = sum(player_army.values())
    total_target_units = sum(target_army.values())

    # Avoid division by zero
    if player_power + target_power > 0:
        # Casualties proportional to opponent power
        player_casualties = min(
            total_player_units,
            int(total_player_units * (target_power / (player_power + target_power)))
        )
        target_casualties = min(
            total_target_units,
            int(total_target_units * (player_power / (player_power + target_power)))
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

def calculate_battle_rewards(outcome, player_army, target_army):
    """
    Returns a string describing the resource rewards or penalties.
    """
    if outcome == "Victory":
        # Simple flat rewards (can be made dynamic later)
        metal_reward = 500
        fuel_reward = 300
        crystal_reward = 50
        return f"{metal_reward} Metal, {fuel_reward} Fuel, {crystal_reward} Crystals"
    elif outcome == "Defeat":
        # Penalty: lose 10% of your resources
        return "Penalty: 10% of your total resources lost."
    else:  # Draw
        return "No rewards (Draw)."
