# modules/building_manager.py

from sheets_service import get_rows, ensure_sheet
from datetime import datetime

# Define per‐level production for each building type
PRODUCTION_PER_LEVEL = {
    'Bank':         ('credits', 20),
    'Mine':         ('minerals', 10),
    'Power Plant':  ('energy',   5),   # <— now matches config.py key
    # add any other production buildings here
}

def get_building_info(user_id: str) -> dict:
    """
    Returns a dict mapping { building_name: level } for this user.
    """
    rows = get_rows('Buildings')
    info = {}
    for row in rows[1:]:
        if row[0] == user_id:
            name, lvl = row[1], int(row[2])
            info[name] = lvl
    return info

def get_production_rates(building_info: dict) -> dict:
    """
    Given building_info (name→level), returns production per minute:
    e.g. { 'credits': 100, 'minerals': 50, 'energy': 20 }
    """
    rates = {'credits': 0, 'minerals': 0, 'energy': 0}
    for bname, lvl in building_info.items():
        if bname in PRODUCTION_PER_LEVEL:
            resource, per_lvl = PRODUCTION_PER_LEVEL[bname]
            rates[resource] += per_lvl * lvl
    return rates

def get_building_health(user_id: str) -> dict:
    """
    Returns { building_name: {'current': int, 'max': int} } for this user.
    Auto-creates the sheet if missing.
    """
    # Ensure the tab exists with correct header
    ensure_sheet('BuildingHealth', ['uid', 'building_name', 'current_hp', 'max_hp'])

    rows = get_rows('BuildingHealth')
    health = {}
    for row in rows[1:]:
        if len(row) < 4 or row[0] != user_id:
            continue
        try:
            current_hp = int(row[2])
            max_hp     = int(row[3])
        except ValueError:
            continue
        health[row[1]] = {'current': current_hp, 'max': max_hp}

    return health
