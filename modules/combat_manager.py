# modules/combat_manager.py

import time
import random
from sheets_service import get_rows, update_row, append_row

def calculate_power(user_id: str) -> int:
    """
    Calculate total combat power for a user_id based on their army composition.
    Infantry = 10 power each
    Tanks    = 50 power each
    Artillery= 100 power each
    """
    army_rows = get_rows('Army')[1:]  # skip header
    power = 0
    for row in army_rows:
        if row[0] != user_id:
            continue
        unit = row[1].lower()
        count = int(row[2])
        if unit == 'infantry':
            power += count * 10
        elif unit == 'tanks':
            power += count * 50
        elif unit == 'artillery':
            power += count * 100
    return power

def attack_player(attacker_id: str, defender_id: str) -> dict:
    """
    Resolve an attack from attacker_id against defender_id.
    Updates credits for both players in the Players sheet and logs to CombatLog.
    Returns a dict: {'result': 'win'|'loss', 'spoils': int}
    """
    # Load and locate player rows
    players = get_rows('Players')
    attacker, defender = None, None
    atk_idx = def_idx = None
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == attacker_id:
            attacker, atk_idx = row.copy(), idx
        if row[0] == defender_id:
            defender, def_idx = row.copy(), idx

    if not attacker or not defender:
        raise ValueError("Attacker or defender not found")

    # Parse credits
    atk_credits = int(attacker[3])
    def_credits = int(defender[3])

    # Compute combat rolls
    atk_power = calculate_power(attacker_id)
    def_power = calculate_power(defender_id)
    atk_roll = atk_power * random.uniform(0.9, 1.1)
    def_roll = def_power * random.uniform(0.9, 1.1)

    timestamp = int(time.time())
    if atk_roll > def_roll:
        result = 'win'
        spoils = max(1, def_credits // 10)
        atk_credits += spoils
        def_credits -= spoils
    else:
        result = 'loss'
        spoils = max(1, atk_credits // 20)
        atk_credits -= spoils
        def_credits += spoils

    # Update Players sheet
    attacker[3] = str(atk_credits)
    defender[3] = str(def_credits)
    update_row('Players', atk_idx, attacker)
    update_row('Players', def_idx, defender)

    # Log combat in CombatLog
    append_row('CombatLog', [
        attacker_id,
        defender_id,
        str(timestamp),
        result,
        str(spoils)
    ])

    return {'result': result, 'spoils': spoils}
