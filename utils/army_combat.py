# army_combat.py

def calculate_battle_outcome(player_army, target_army):
    player_power = sum([UNIT_STATS.get(unit, {}).get("attack", 0) * count for unit, count in player_army.items()])
    target_power = sum([UNIT_STATS.get(unit, {}).get("attack", 0) * count for unit, count in target_army.items()])

    if player_power > target_power:
        return "Victory"
    elif player_power < target_power:
        return "Defeat"
    else:
        return "Draw"

