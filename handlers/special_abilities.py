# modules/special_abilities.py
from sheets_service import get_rows, update_row, append_row

ABILITIES = {
    'infantry': [
        {'id': 'crit strike', 'name': 'Critical Strike', 'effect': '20% chance to deal double damage', 'cost': 100},
        {'id': 'rapid fire', 'name': 'Rapid Fire', 'effect': ' Increases attack speed for 10 seconds', 'cost': 200}
    ],
    'tanks': [
        {'id': 'shield wall', 'name': 'Shield Wall', 'effect': 'Reduces incoming damage by 30% for 15 seconds', 'cost': 150},
        {'id': 'charge', 'name': 'Charge', 'effect': 'Deals bonus damage and stuns enemies briefly', 'cost': 250}
    ],
    'artillery': [
        {'id': 'precision aim', 'name': 'Precision Aim', 'effect': 'Increases accuracy and critical hit chance', 'cost': 200},
        {'id': 'area bombard', 'name': 'Area Bombardment', 'effect': 'Deals splash damage to multiple enemies', 'cost': 300}
    ]
}

def get_unit_abilities(unit_type: str):
    return ABILITIES.get(unit_type.lower(), [])

def purchase_ability(user_id: str, unit_type: str, ability_id: str):
    players = get_rows('Players')
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == user_id:
            current_credits = int(row[3])
            premium_credits = int(row[7]) if len(row) > 7 else 0
            ability = next((a for a in ABILITIES[unit_type] if a['id'] == ability_id), None)
            if not ability:
                return False, "Ability not found"
            if premium_credits < ability['cost']:
                return False, "Insufficient premium credits"
            new_premium = premium_credits - ability['cost']
            while len(row) < 8:
                row.append('0')
            row[7] = str(new_premium)
            update_row('Players', idx, row)
            # Record purchased ability
            abilities = get_rows('UnitAbilities')
            append_row('UnitAbilities', [user_id, unit_type, ability_id, '1'])
            return True, f"Successfully purchased {ability['name']}!"
    return False, "Player not found"

def use_ability(user_id: str, unit_type: str, ability_id: str):
    # Logic to use the ability in combat
    pass
