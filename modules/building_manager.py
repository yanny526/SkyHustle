# modules/building_manager.py

from sheets_service import get_rows
from datetime import datetime

# Define per‐level production for each building type
PRODUCTION_PER_LEVEL = {
    'Bank':       ('credits', 20),
    'Mine':       ('minerals', 10),
    'PowerPlant': ('energy', 5),
    # add any other production buildings here
}

def get_building_info(user_id: str) -> dict:
    """
    Returns { building_name: level } for this user.
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
    Returns { building_name: {'current': int, 'max': int} }.
    Expects a 'BuildingHealth' sheet with columns: [uid, name, current_hp, max_hp].
    """
    rows = get_rows('BuildingHealth')
    health = {}
    for row in rows[1:]:
        if row[0] == user_id and len(row) >= 4:
            name, cur, mx = row[1], int(row[2]), int(row[3])
            health[name] = {'current': cur, 'max': mx}
    return health
