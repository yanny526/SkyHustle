# modules/upgrade_manager.py

import time
from sheets_service import get_rows, append_row, clear_range

# Range of the Upgrades sheet (columns A–E)
UPGRADES_RANGE = 'Upgrades!A:E'

async def initiate_upgrade(user_id: str, building: str, current_lvl: int, duration: int):
    """
    Schedule a new building upgrade for user_id.
    building: name of building (e.g., 'Barracks')
    current_lvl: its current level
    duration: seconds until completion
    """
    start_ts = int(time.time())
    target_lvl = current_lvl + 1
    append_row(UPGRADES_RANGE, [user_id, building, str(target_lvl), str(start_ts), str(duration)])


def complete_upgrades(user_id: str) -> None:
    """
    Check the Upgrades sheet for any finished upgrades for user_id,
    apply them and remove completed rows.
    """
    rows = get_rows(UPGRADES_RANGE)
    if not rows or len(rows) < 2:
        return
    header, *data = rows
    keep = []
    now = int(time.time())
    for row in data:
        if len(row) < 5:
            continue
        uid, building, target_str, start_str, dur_str = row
        start = int(start_str)
        dur   = int(dur_str)
        finish = start + dur
        if uid == user_id and now >= finish:
            # apply upgrade
            from modules.building_manager import set_building_level
            set_building_level(user_id, building, int(target_str))
        else:
            keep.append(row)
    # rewrite the sheet: clear and re-append header + remaining
    clear_range(UPGRADES_RANGE)
    append_row(UPGRADES_RANGE, header)
    for r in keep:
        append_row(UPGRADES_RANGE, r)


def get_pending_upgrades(user_id: str) -> list[tuple[str,int,str]]:
    """
    Return a list of (building, target_level, remaining_time_str) for all
    upgrades still in progress for user_id.
    """
    rows = get_rows(UPGRADES_RANGE)
    if not rows or len(rows) < 2:
        return []
    pending = []
    now = int(time.time())
    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        uid, building, target_str, start_str, dur_str = row
        if uid != user_id:
            continue
        start = int(start_str)
        dur   = int(dur_str)
        rem = start + dur - now
        if rem > 0:
            h = rem // 3600
            m = (rem % 3600) // 60
            s = rem % 60
            pending.append((building, int(target_str), f"{h:02d}:{m:02d}:{s:02d}"))
    return pending
