# modules/upgrade_manager.py

from datetime import datetime
from sheets_service import get_rows, update_row, append_row
from config import BUILDING_MAX_LEVEL

def complete_upgrades(user_id: str):
    """
    Check the 'Upgrades' sheet for any finished builds,
    apply their new levels, and remove the completed rows.
    """
    rows = get_rows('Upgrades')
    header, data = rows[0], rows[1:]
    now_ts = datetime.utcnow().timestamp()

    # We'll rebuild the sheet without the completed ones:
    new_data = []
    for row in data:
        uid, bname, start_ts, end_ts, target_lvl = row[:5]
        if uid != user_id:
            new_data.append(row)
            continue

        if now_ts >= float(end_ts):
            # Apply the new level in Buildings sheet
            apply_building_level(uid, bname, int(target_lvl))
        else:
            new_data.append(row)

    # Overwrite the Upgrades sheet (header + new_data)
    # (Assuming update_row and append_row logic in your project supports this)
    # First clear it, then re-add header + new_data:
    clear_sheet('Upgrades')
    append_row('Upgrades', header)
    for r in new_data:
        append_row('Upgrades', r)

def apply_building_level(uid: str, building: str, new_level: int):
    """
    Internal helper: writes the upgraded building level into 'Buildings' sheet.
    """
    b_rows = get_rows('Buildings')
    for idx, row in enumerate(b_rows[1:], start=1):
        if row[0] == uid and row[1] == building:
            row[2] = str(new_level)
            update_row('Buildings', idx, row)
            return

    # If not found, add a new entry:
    append_row('Buildings', [uid, building, str(new_level)])

# --- New helper for your /status command ---

def get_pending_upgrades(uid: str) -> list[tuple[str, str, str]]:
    """
    Return a list of (building_name, target_level, remaining_str)
    for any upgrades still in progress for this user.
    """
    # Pull all rows from the “Upgrades” sheet (skip header)
    rows = get_rows('Upgrades')[1:]
    pending = []
    now_ts = datetime.utcnow().timestamp()

    for r in rows:
        # Expecting at least [uid, building, start_ts, end_ts, target_level]
        if len(r) < 5 or r[0] != uid:
            continue

        bname      = r[1]
        end_ts     = float(r[3])
        target_lvl = r[4]
        rem_seconds = end_ts - now_ts

        if rem_seconds > 0:
            hrs, rem = divmod(int(rem_seconds), 3600)
            mins, secs = divmod(rem, 60)
            remaining_str = f\"{hrs:02d}:{mins:02d}:{secs:02d}\"
            pending.append((bname, target_lvl, remaining_str))

    return pending
