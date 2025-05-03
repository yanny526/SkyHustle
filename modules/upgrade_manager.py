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
    If the sheet is missing or invalid, returns {}.
    """
    try:
        rows = get_rows('BuildingHealth')
    except Exception:
        # Sheet not found or bad range → no health data
        return {}

    if not rows or len(rows) < 2:
        return {}

    health = {}
    for row in rows[1:]:
        if len(row) < 4 or row[0] != user_id:
            continue
        name = row[1]
        try:
            current_hp = int(row[2])
            max_hp = int(row[3])
        except ValueError:
            continue
        health[name] = {'current': current_hp, 'max': max_hp}

    return health
