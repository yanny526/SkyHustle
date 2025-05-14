import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError

from sheets_service import get_rows, update_row, append_row, ensure_sheet

logger = logging.getLogger(__name__)

# Sheet names
BUILDINGS_SHEET      = "Buildings"        # columns: uid, building_name, level, end_ts
BUILD_HEALTH_SHEET   = "BuildingHealth"   # unchanged
COMPLETED_BUILD_SHEET= "CompletedBuilds"  # new sheet to record history

# Per‐level production unchanged
PRODUCTION_PER_LEVEL = {
    'Bank':         ('credits', 20),
    'Mine':         ('minerals', 10),
    'Power Plant':  ('energy',   5),
}


def get_building_info(user_id: str) -> dict:
    """
    Returns { building_name -> level } for this user.
    """
    rows = get_rows(BUILDINGS_SHEET)
    info = {}
    for row in rows[1:]:
        if row[0] == user_id:
            name, lvl = row[1], int(row[2] or 0)
            info[name] = lvl
    return info


def get_production_rates(building_info: dict) -> dict:
    """
    Given building_info (name→level), returns production per minute.
    """
    rates = {'credits': 0, 'minerals': 0, 'energy': 0}
    for bname, lvl in building_info.items():
        if bname in PRODUCTION_PER_LEVEL:
            resource, per_lvl = PRODUCTION_PER_LEVEL[bname]
            rates[resource] += per_lvl * lvl
    return rates


def get_building_health(user_id: str) -> dict:
    """
    Returns { building_name: {'current','max'} }.
    """
    ensure_sheet(BUILD_HEALTH_SHEET, ['uid','building_name','current_hp','max_hp'])
    rows = get_rows(BUILD_HEALTH_SHEET)
    health = {}
    for row in rows[1:]:
        if len(row)>=4 and row[0]==user_id:
            try:
                current_hp = int(row[2]); max_hp = int(row[3])
            except ValueError:
                continue
            health[row[1]] = {'current': current_hp, 'max': max_hp}
    return health


# ─── BUILD QUEUE APIs ─────────────────────────────────────────────────────────


def get_build_queue(user_id: str) -> list[dict]:
    """
    Return pending upgrades for this user:
      [{ building: str, level: int, remaining_sec: int }, ...]
    """
    try:
        rows = get_rows(BUILDINGS_SHEET)
    except HttpError as e:
        logger.error("get_build_queue: failed to load '%s': %s", BUILDINGS_SHEET, e)
        return []

    header, *data = rows
    now = time.time()
    queue = []
    for r in data:
        if len(r)<4 or r[0]!=user_id or not r[3]:
            continue
        try:
            end_ts = float(r[3])
        except ValueError:
            continue
        if end_ts > now:
            queue.append({
                'building': r[1],
                'level': int(r[2] or 0)+1,
                'remaining_sec': int(end_ts - now),
            })
    return queue


def cancel_build(user_id: str, building: str) -> bool:
    """
    Cancel a queued upgrade. Returns True if found & cleared.
    """
    try:
        rows = get_rows(BUILDINGS_SHEET)
    except HttpError as e:
        logger.error("cancel_build: failed to load '%s': %s", BUILDINGS_SHEET, e)
        return False

    header, *data = rows
    for idx, r in enumerate(data, start=1):
        if len(r)>=4 and r[0]==user_id and r[1]==building and r[3]:
            # clear the end_ts field
            new = r.copy()
            new[3] = ""
            update_row(BUILDINGS_SHEET, idx, new)
            return True
    return False


def complete_build_job(context):
    """
    Periodic job: for each row whose end_ts <= now, increment its level,
    record in COMPLETED_BUILD_SHEET, and clear end_ts.
    """
    now = time.time()

    # Ensure history sheet exists
    ensure_sheet(COMPLETED_BUILD_SHEET, ['uid','building_name','old_level','new_level','completed_at'])

    try:
        rows = get_rows(BUILDINGS_SHEET)
    except HttpError as e:
        logger.error("complete_build_job: failed to load '%s': %s", BUILDINGS_SHEET, e)
        return

    header, *data = rows
    for idx, r in enumerate(data, start=1):
        if len(r) < 4 or not r[3]:
            continue
        try:
            end_ts = float(r[3])
        except ValueError:
            continue
        if end_ts <= now:
            uid, bname = r[0], r[1]
            try:
                old_level = int(r[2] or 0)
            except ValueError:
                old_level = 0
            new_level = old_level + 1

            # 1) Record history
            ts_iso = datetime.utcnow().isoformat()
            append_row(COMPLETED_BUILD_SHEET, [uid, bname, str(old_level), str(new_level), ts_iso])

            # 2) Update building row: set new level, clear end_ts
            new_row = [uid, bname, str(new_level), ""]
            update_row(BUILDINGS_SHEET, idx, new_row)
