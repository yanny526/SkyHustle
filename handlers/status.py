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
        if len(row) < 5:
            continue
        uid, bname, start_ts, end_ts, target_lvl = row[:5]

        if uid != user_id:
            new_data.append(row)
            continue

        try:
            if now_ts >= float(end_ts):
                apply_building_level(uid, bname, int(target_lvl))
                continue
        except ValueError:
            continue

        new_data.append(row)

    clear_sheet('Upgrades')
    append_row('Upgrades', header)
    for r in new_data:
        append_row('Upgrades', r)


def apply_building_level(uid: str, building: str, new_level: int):
    """
    Internal helper: writes the upgraded building level into the 'Buildings' sheet.
    """
    b_rows = get_rows('Buildings')
    if not b_rows:
        return

    for idx, row in enumerate(b_rows[1:], start=1):
        if len(row) >= 2 and row[0] == uid and row[1] == building:
            capped = min(new_level, BUILDING_MAX_LEVEL.get(building, new_level))
            row[2:3] = [str(capped)]
            update_row('Buildings', idx, row)
            return

    capped = min(new_level, BUILDING_MAX_LEVEL.get(building, new_level))
    append_row('Buildings', [uid, building, str(capped)])


def get_pending_upgrades(user_id: str) -> list[dict]:
    """
    Fetch all pending upgrades for the given user.
    Returns a list of dicts, each with:
      - 'bname': building name (str)
      - 'target_lvl': level to reach (int)
      - 'end_ts': UNIX timestamp when it completes (float)
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
            end_ts = float(end_ts)
        except ValueError:
            continue
        if end_ts > now_ts:
            pending.append({
                'bname': bname,
                'target_lvl': int(target_lvl),
                'end_ts': end_ts
            })

    return pending
