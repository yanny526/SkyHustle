# modules/upgrade_manager.py

import time
from sheets_service import get_rows, update_row
from config import BUILDING_MAX_LEVEL


def complete_upgrades(user_id: str):
    """
    For each building upgrade whose end_ts has passed:
    - Increase the building's level if below cap.
    - Clear the upgrade timestamp.
    """
    rows = get_rows('Buildings')
    now = int(time.time())

    # Skip header row; enumerate idx starts at 1 for sheet indexing
    for idx, row in enumerate(rows[1:], start=1):
        # Need at least 4 columns: uid, building, level, end_ts
        if len(row) < 4:
            continue
        uid, btype, lvl_str, ts_str = row[0], row[1], row[2], row[3]
        if uid != user_id or not ts_str:
            continue

        # Parse end timestamp
        try:
            end_ts = int(float(ts_str))
        except (ValueError, TypeError):
            # Invalid timestamp; clear it
            row[3] = ''
            update_row('Buildings', idx, row)
            continue

        # If upgrade has completed:
        if now >= end_ts:
            # Determine current level
            curr_lvl = int(lvl_str) if lvl_str.isdigit() else 0
            max_lvl = BUILDING_MAX_LEVEL.get(btype)
            if max_lvl is not None and curr_lvl >= max_lvl:
                # At cap: just clear the timestamp
                row[3] = ''
                update_row('Buildings', idx, row)
                continue

            # Perform the level-up
            row[2] = str(curr_lvl + 1)
            row[3] = ''
            update_row('Buildings', idx, row)


def get_pending_upgrades(user_id: str) -> list[tuple[str, str, str]]:
    """
    Return a list of (building_name, target_level, remaining_time_str)
    for all upgrades still in progress for this user.
    """
    rows = get_rows('Upgrades')[1:]  # skip header
    pending = []
    now_ts = time.time()

    for r in rows:
        # Expect at least [uid, building, start_ts, end_ts, target_level]
        if len(r) < 5 or r[0] != user_id:
            continue
        bname      = r[1]
        end_ts_str = r[3]
        target_lvl = r[4]

        try:
            end_ts = float(end_ts_str)
        except (ValueError, TypeError):
            continue

        rem = end_ts - now_ts
        if rem > 0:
            hrs, rem_sec = divmod(int(rem), 3600)
            mins, secs  = divmod(rem_sec, 60)
            remaining = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            pending.append((bname, target_lvl, remaining))

    return pending
