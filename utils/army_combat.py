import json

# Load unit stats from config
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)

# Load battle tactics
with open("config/battle_tactics.json", "r") as f:
    BATTLE_TACTICS = json.load(f)


def calculate_battle_outcome(
    player_army: dict[str, int],
    target_army: dict[str, int],
    tactic_name: str,
) -> tuple[str, str]:
    """
    Calculates battle outcome applying tactic bonuses.

    Args:
        player_army: Attacker's unit counts
        target_army: Defender's unit counts
        tactic_name: Key for chosen tactic in BATTLE_TACTICS

    Returns:
        outcome: "Victory", "Defeat", or "Draw"
        battle_log: Summary of power and casualties
    """
    tactic = BATTLE_TACTICS.get(tactic_name, {})

    def compute_power(army: dict[str, int]) -> float:
        total = 0.0
        for unit, count in army.items():
            stats = UNIT_STATS.get(unit, {})
            base_atk = stats.get("attack", 0)
            role = stats.get("role")
            bonus = 0.0
            if role and "attack_bonus" in tactic:
                bonus = tactic["attack_bonus"].get(role, 0.0)
            total += (base_atk * (1 + bonus)) * count
        return total

    player_power = compute_power(player_army)
    target_power = compute_power(target_army)

    total_player = sum(player_army.values())
    total_target = sum(target_army.values())

    player_casualties = target_casualties = 0
    if player_power + target_power > 0:
        player_casualties = min(
            total_player,
            int(total_player * (target_power / (player_power + target_power)))
        )
        target_casualties = min(
            total_target,
            int(total_target * (player_power / (player_power + target_power)))
        )

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
    player_army: dict[str, int],
    target_army: dict[str, int],
) -> str:
    """
    Returns resource rewards or penalties.

    Args:
        outcome: Battle outcome
        player_army: Attacker's army
        target_army: Defender's army

    Returns:
        Formatted rewards string
    """
    if outcome == "Victory":
        return "500 Metal, 300 Fuel, 50 Crystals"
    if outcome == "Defeat":
        return "Penalty: 10% of your total resources lost."
    return "No rewards (Draw)."
