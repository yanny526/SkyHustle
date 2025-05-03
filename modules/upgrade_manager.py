# modules/upgrade_manager.py

import time
from sheets_service import get_rows, update_row
from config import BUILDING_MAX_LEVEL

def complete_upgrades(user_id: str):
    """
    For each building upgrade whose end_ts has passed, bump the level
    and clear the upgrade timestamp.
    """
    rows = get_rows('Buildings')
    now = int(time.time())

    # rows[0] is header; enumerate starts at 1 to match sheet row indices
    for idx, row in enumerate(rows[1:], start=1):
        if row[0] == user_id and row[3]:
            end_ts = int(row[3])
            if now >= end_ts:
                current_lvl = int(row[2])
                row[2] = str(current_lvl + 1)  # new level
                row[3] = ''                   # clear upgrade timestamp
                update_row('Buildings', idx, row)

def get_pending_upgrades(user_id: str) -> list:
    """
    Returns a list of (building_type, next_level, seconds_remaining)
    for all upgrades still in progress.
    """
    pending = []
    now = int(time.time())
    rows = get_rows('Buildings')[1:]

    for row in rows:
        if row[0] == user_id and row[3]:
            btype = row[1]
            current_lvl = int(row[2])
            next_lvl = current_lvl + 1
            end_ts = int(row[3])
            rem = max(0, end_ts - now)
            pending.append((btype, next_lvl, rem))

    return pending
