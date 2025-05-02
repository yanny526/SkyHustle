# modules/upgrade_manager.py

import time
from sheets_service import get_rows, update_row
from config import BUILDING_MAX_LEVEL

def complete_upgrades(uid: str):
    """
    Check the Buildings sheet for any upgrades that have finished.
    For each finished upgrade:
     - If the building is below its max level, bump the level and clear the timestamp.
     - If it’s already at or above the cap, just clear the timestamp.
    Returns a list of (building_type, new_level) for actual upgrades performed.
    """
    rows = get_rows('Buildings')
    now = time.time()
    completed = []

    for idx, row in enumerate(rows[1:], start=1):
        # Skip if it isn’t this user or there’s no pending timestamp
        if row[0] != uid or len(row) < 4 or not row[3]:
            continue

        btype = row[1]
        try:
            end_ts = float(row[3])
        except ValueError:
            # Bad data—wipe the timestamp so we don’t loop forever
            row[3] = ''
            update_row('Buildings', idx, row)
            continue

        # Not done yet?
        if end_ts > now:
            continue

        # Current level and cap
        lvl = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
        max_lvl = BUILDING_MAX_LEVEL.get(btype)

        if max_lvl is not None and lvl >= max_lvl:
            # Already at cap: clear timestamp, no upgrade
            row[3] = ''
            update_row('Buildings', idx, row)
            continue

        # Perform the upgrade
        new_lvl = lvl + 1
        row[2] = str(new_lvl)
        row[3] = ''
        update_row('Buildings', idx, row)
        completed.append((btype, new_lvl))

    return completed
