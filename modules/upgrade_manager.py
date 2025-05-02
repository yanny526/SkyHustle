# modules/upgrade_manager.py

import time
from sheets_service import get_rows, update_row, append_row

def get_cost_and_duration(building_type: str, current_level: int) -> tuple:
    """
    Calculate cost (credits, minerals) and duration (seconds)
    for upgrading `building_type` from current_level to current_level+1.
    """
    L = current_level + 1
    if building_type == 'Mine':
        cost_credits = 100
        cost_minerals = 50 * L
        duration = 30 * 60 * L
    elif building_type == 'Power Plant':
        cost_credits = 100
        cost_minerals = 30 * L
        duration = 20 * 60 * L
    elif building_type == 'Barracks':
        cost_credits = 150
        cost_minerals = 70 * L
        duration = 45 * 60 * L
    elif building_type == 'Workshop':
        cost_credits = 200
        cost_minerals = 100 * L
        duration = 60 * 60 * L
    else:
        raise ValueError(f"Unknown building: {building_type}")
    return cost_credits, cost_minerals, duration

def start_upgrade(user_id: str, building_type: str):
    """
    Deduct resources and schedule an upgrade for `building_type`.
    Returns (cost_credits, cost_minerals, duration).
    Raises ValueError on insufficient resources.
    """
    # Fetch current player resources
    players = get_rows('Players')
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == user_id:
            prow = row.copy()
            prow_idx = idx
            break
    else:
        raise ValueError("User not found")

    credits = int(prow[3])
    minerals = int(prow[4])

    # Fetch current building level
    buildings = get_rows('Buildings')
    current_level = 0
    build_row = None
    for idx, row in enumerate(buildings[1:], start=1):
        if row[0] == user_id and row[1] == building_type:
            current_level = int(row[2]) if len(row) > 2 else 0
            build_row = (idx, row.copy())
            break

    # Calculate cost & duration
    cost_credits, cost_minerals, duration = get_cost_and_duration(building_type, current_level)

    # Check resources
    if credits < cost_credits or minerals < cost_minerals:
        raise ValueError("Insufficient resources")

    # Deduct and update
    prow[3] = str(credits - cost_credits)
    prow[4] = str(minerals - cost_minerals)
    update_row('Players', prow_idx, prow)

    # Schedule upgrade
    end_ts = time.time() + duration
    if build_row:
        b_idx, brow = build_row
        # ensure we have at least 4 columns
        while len(brow) < 4:
            brow.append('')
        brow[3] = str(end_ts)
        update_row('Buildings', b_idx, brow)
    else:
        append_row('Buildings', [user_id, building_type, str(current_level), str(end_ts)])

    return cost_credits, cost_minerals, duration

def get_pending_upgrades(user_id: str) -> list:
    """
    Return list of (building_type, next_level, end_ts)
    for all in-progress upgrades of user_id.
    """
    pending = []
    now = time.time()
    for row in get_rows('Buildings')[1:]:
        if row[0] != user_id:
            continue
        lvl = int(row[2]) if len(row) > 2 else 0
        end_ts = float(row[3]) if len(row) > 3 and row[3] else 0
        if end_ts > now:
            pending.append((row[1], lvl + 1, end_ts))
    return pending

def complete_upgrades(user_id: str) -> list:
    """
    Process any finished upgrades: increments level and clears end_ts.
    Returns list of (building_type, new_level) for completed ones.
    """
    completed = []
    now = time.time()
    rows = get_rows('Buildings')
    for idx, row in enumerate(rows[1:], start=1):
        # only proceed if there's an end_ts column
        if row[0] == user_id and len(row) > 3 and row[3]:
            end_ts = float(row[3])
            if end_ts <= now:
                new_lvl = int(row[2]) + 1 if len(row) > 2 else 1
                row[2] = str(new_lvl)
                row[3] = ''
                update_row('Buildings', idx, row)
                completed.append((row[1], new_lvl))
    return completed
