# modules/unit_manager.py

from config import TIER_UNLOCK
from sheets_service import get_rows

# Unit definitions: key -> (display_name, emoji, tier, power, cost_dict)
UNITS = {
    'infantry':         ('Infantry',       '👨‍✈️', 1,  10, {'c':  10, 'm':  5, 'e':  1}),
    'tanks':            ('Tanks',          '🛡️',   1,  50, {'c': 100, 'm': 50, 'e':  5}),
    'artillery':        ('Artillery',      '🚀',   1, 100, {'c': 200, 'm':100, 'e': 10}),
    'heavy_infantry':   ('Heavy Infantry','🔰',   2,  25, {'c':  50, 'm': 25, 'e':  2}),
    'assault_tank':     ('Assault Tank',   '🚜',   2, 150, {'c': 300, 'm':150, 'e':  8}),
    'rocket_launcher':  ('Rocket Launcher','🧨',   2, 250, {'c': 500, 'm':300, 'e': 12}),
    'mech_infantry':    ('Mech Infantry', '🤖',   3,  50, {'c': 150, 'm':100, 'e':  5}),
    'battle_tank':      ('Battle Tank',    '🏹',   3, 300, {'c': 800, 'm':400, 'e': 15}),
    'siege_cannon':     ('Siege Cannon',   '🏰',   3, 500, {'c':1200, 'm':800, 'e': 20}),
}

def get_building_levels(uid: str) -> dict:
    """Return a dict of building levels for a user."""
    rows = get_rows('Buildings')[1:]
    levels = {}
    for r in rows:
        if r[0] != uid:
            continue
        btype = r[1]
        lvl = int(r[2]) if len(r) > 2 and r[2].isdigit() else 0
        levels[btype] = lvl
    return levels


def get_unlocked_tier(uid: str) -> int:
    """Compute highest unit tier unlocked based on building requirements."""
    levels = get_building_levels(uid)
    unlocked = 1
    for tier, reqs in TIER_UNLOCK.items():
        if all(levels.get(b, 0) >= req for b, req in reqs.items()):
            unlocked = max(unlocked, tier)
    return unlocked


def get_available_units(uid: str) -> dict:
    """Return units (key->info) available to train for this user."""
    tier = get_unlocked_tier(uid)
    return {k: v for k, v in UNITS.items() if v[2] == tier}


def get_all_units_by_tier() -> dict:
    """Group all units by their tier, returning 5‑tuple (key, display, emoji, power, cost)."""
    from collections import defaultdict
    units = defaultdict(list)
    for key, info in UNITS.items():
        display, emoji, t, power, cost = info
        units[t].append((key, display, emoji, power, cost))
    return units
