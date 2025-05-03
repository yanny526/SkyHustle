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

def get_pending_upgrades(uid: str) -> list[tuple[str, str, str]]:
    """
    Return a list of (building_name, target_level, remaining_str)
    for any upgrades still in progress for this user.
    """
    rows = get_rows('Upgrades')[1:]  # skip header
    pending = []
    now_ts = datetime.utcnow().timestamp()

    for r in rows:
        if len(r) < 5 or r[0] != uid:
            continue

        bname = r[1]
        try:
            end_ts = float(r[3])
        except (ValueError, IndexError):
            continue
        target_lvl = r[4]
        rem_seconds = end_ts - now_ts
        if rem_seconds > 0:
            hrs, rem = divmod(int(rem_seconds), 3600)
            mins, secs = divmod(rem, 60)
            remaining_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            pending.append((bname, target_lvl, remaining_str))

    return pending
