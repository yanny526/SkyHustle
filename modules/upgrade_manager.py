# modules/upgrade_manager.py

from datetime import datetime
from sheets_service import get_rows, update_row, append_row, clear_range
from config import BUILDING_MAX_LEVEL

def complete_upgrades(user_id: str) -> None:
    """
    Check the 'Upgrades' sheet for any finished builds for this user,
    apply their new levels, and rebuild the sheet without completed rows.
    """
    rows = get_rows('Upgrades')
    if not rows:
        return

    header, data = rows[0], rows[1:]
    now_ts = datetime.utcnow().timestamp()

    new_data = []
    for row in data:
        # skip any malformed row
        if len(row) < 5:
            continue

        uid, building, start_ts, end_ts, target_lvl = row[:5]
        if uid != user_id:
            new_data.append(row)
            continue

        # try parsing end timestamp
        try:
            end_ts_f = float(end_ts)
        except ValueError:
            # can't parse, keep it around and move on
            new_data.append(row)
            continue

        if now_ts >= end_ts_f:
            # complete it
            lvl = int(target_lvl)
            # enforce your global cap if defined
            max_lvl = BUILDING_MAX_LEVEL.get(building)
            if max_lvl is not None and lvl > max_lvl:
                lvl = max_lvl
            apply_building_level(uid, building, lvl)
        else:
            new_data.append(row)

    # clear out the entire sheet and rewrite header + pending rows
    clear_range('Upgrades')
    append_row('Upgrades', header)
    for r in new_data:
        append_row('Upgrades', r)


def apply_building_level(uid: str, building: str, new_level: int) -> None:
    """
    Write the upgraded building level into the 'Buildings' sheet,
    either updating an existing row or appending a new one.
    """
    b_rows = get_rows('Buildings')
    if not b_rows:
        # nothing at all? add header? (optional)
        pass

    # look for existing entry
    for idx, row in enumerate(b_rows[1:], start=2):
        if len(row) >= 2 and row[0] == uid and row[1] == building:
            # write back the new_level
            update_row('Buildings', idx, [uid, building, str(new_level)])
            return

    # not found → append
    append_row('Buildings', [uid, building, str(new_level)])


def get_pending_upgrades(uid: str) -> list[tuple[str, str, str]]:
    """
    Return [(building, target_level, time_remaining)] for any
    upgrades still in progress for this user.
    """
    rows = get_rows('Upgrades')
    if not rows:
        return []

    pending = []
    now_ts = datetime.utcnow().timestamp()
    for row in rows[1:]:
        if len(row) < 5 or row[0] != uid:
            continue

        building = row[1]
        try:
            end_ts = float(row[3])
        except ValueError:
            continue

        rem = end_ts - now_ts
        if rem > 0:
            hrs, rem = divmod(int(rem), 3600)
            mins, secs = divmod(rem, 60)
            remaining_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            pending.append((building, row[4], remaining_str))

    return pending
