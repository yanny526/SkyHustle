import json
from datetime import datetime
from typing import Dict, Tuple

# Load unit stats from config
with open("os.path.join(os.path.dirname(__file__), "../config/army_stats.json")", "r") as f:
    UNIT_STATS = json.load(f)

# Load battle tactics\ nwith open("config/battle_tactics.json", "r") as f:
    BATTLE_TACTICS = json.load(f)

# Load unit abilities
with open("config/unit_abilities.json", "r") as f:
    UNIT_ABILITIES = json.load(f)


def calculate_battle_outcome(
    player_army: Dict[str, int],
    target_army: Dict[str, int],
    tactic_name: str = ""
) -> Tuple[str, str]:
    """
    Calculates the battle outcome applying tactic and ability modifiers.

    Args:
        player_army: Dict of unit_name → count for attacker.
        target_army: Dict of unit_name → count for defender.
        tactic_name: Selected tactic key.

    Returns:
        Tuple of (outcome, battle_log).
    """
    tactic = BATTLE_TACTICS.get(tactic_name, {})

    def apply_modifiers(army: Dict[str, int]) -> float:
        total = 0.0
        for unit, count in army.items():
            stats = UNIT_STATS.get(unit, {})
            atk = stats.get("attack", 0)
            defp = stats.get("defense", 0)
            spd = stats.get("speed", 0)
            role = stats.get("role")

            # Tactic modifiers
            if role:
                if "attack_bonus" in tactic:
                    atk *= 1 + tactic["attack_bonus"].get(role, 0)
                if "defense_penalty" in tactic:
                    defp *= 1 - tactic["defense_penalty"].get(role, 0)
                if "speed_bonus" in tactic:
                    spd *= 1 + tactic["speed_bonus"].get(role, 0)
                if "speed_penalty" in tactic:
                    spd *= 1 - tactic["speed_penalty"].get(role, 0)

            # Ability modifiers
            for ability_key in stats.get("abilities", []):
                ability = UNIT_ABILITIES.get(ability_key, {})
                trigger = ability.get("trigger")
                if trigger in ("passive", "start_of_battle"):
                    if "attack_bonus" in ability:
                        atk *= 1 + ability["attack_bonus"]
                    if "defense_penetration" in ability:
                        atk *= 1 + ability["defense_penetration"]
                    if "speed_bonus" in ability:
                        spd *= 1 + ability["speed_bonus"]
                    if "speed_penalty" in ability:
                        spd *= 1 - ability["speed_penalty"]

            total += atk * count
        return total

    player_power = apply_modifiers(player_army)
    target_power = apply_modifiers(target_army)

    total_player = sum(player_army.values())
    total_target = sum(target_army.values())

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

    if player_power > target_power:
        outcome = "Victory"
    elif player_power < target_power:
        outcome = "Defeat"
    else:
        outcome = "Draw"

    battle_log = (
        f"Your Power: {int(player_power)}  |  Enemy Power: {int(target_power)}\n"
        f"You lost {player_casualties} unit(s), Enemy lost {target_casualties} unit(s)."
    )

    return outcome, battle_log


def calculate_battle_rewards(
    outcome: str,
    player_army: Dict[str, int],
    target_army: Dict[str, int]
) -> str:
    """
    Returns resource rewards or penalties based on outcome.
    """
    if outcome == "Victory":
        return "500 Metal, 300 Fuel, 50 Crystals"
    if outcome == "Defeat":
        return "Penalty: 10% of your total resources lost."
    return "No rewards (Draw)."
