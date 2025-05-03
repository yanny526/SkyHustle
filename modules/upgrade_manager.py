# modules/upgrade_manager.py

from datetime import datetime
from sheets_service import get_rows, update_row, append_row, clear_sheet
from config import BUILDING_MAX_LEVEL

def complete_upgrades(user_id: str):
    """
    Check the 'Upgrades' sheet for any finished builds,
    apply their new levels, and rebuild the sheet without completed rows.
    """
    rows = get_rows('Upgrades')
    if not rows:
        return
    header, data = rows[0], rows[1:]
    now_ts = datetime.utcnow().timestamp()

    new_data = []
    for row in data:
        # Ensure we have at least 5 columns
        if len(row) < 5:
            continue
        uid, bname, start_ts, end_ts, target_lvl = row[:5]

        if uid != user_id:
            new_data.append(row)
            continue

        # If upgrade is finished, apply it; otherwise keep it pending
        try:
            if now_ts >= float(end_ts):
                apply_building_level(uid, bname, int(target_lvl))
                continue
        except ValueError:
            # malformed timestamp, drop the row
            continue

        new_data.append(row)

    # Clear everything below the header, then re-append
    clear_sheet('Upgrades')
    append_row('Upgrades', header)
    for r in new_data:
        append_row('Upgrades', r)


def apply_building_level(uid: str, building: str, new_level: int):
    """
    Internal helper: writes the upgraded building level into 'Buildings' sheet.
    """
    b_rows = get_rows('Buildings')
    if not b_rows:
        # ensure header exists, but this shouldn't normally happen
        return

    # Look for existing entry
    for idx, row in enumerate(b_rows[1:], start=1):
        if len(row) >= 2 and row[0] == uid and row[1] == building:
            # Cap the level
            capped = min(new_level, BUILDING_MAX_LEVEL.get(building, new_level))
            row[2:3] = [str(capped)]
            update_row('Buildings', idx, row)
            return

    # Not found: append new
    capped = min(new_level, BUILDING_MAX_LEVEL.get(building, new_level))
    append_row('Buildings', [uid, building, str(capped)])


def get_pending_upgrades(user_id: str) -> list[dict]:
    """
    Fetch all pending upgrades for the given user.
    Returns a list of dicts:
      {'bname': str, 'target_lvl': int, 'end_ts': float}
    """
    rows = get_rows('Upgrades')
    pending = []
    now_ts = datetime.utcnow().timestamp()

    for row in rows[1:]:
        if len(row) < 5:
            continue
        uid, bname, start_ts, end_ts, target_lvl = row[:5]
        if uid != user_id:
            continue
        try:
            end = float(end_ts)
        except ValueError:
            continue
        if end > now_ts:
            pending.append({
                'bname': bname,
                'target_lvl': int(target_lvl),
                'end_ts': end
            })

    return pending
