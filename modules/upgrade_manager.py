from datetime import datetime
from sheets_service import get_rows, append_row, clear_range

UPGRADES_RANGE = "Upgrades!A:E"
HEADER_ROW     = ["user_id", "building_key", "target_level", "start_ts", "duration_secs"]

def schedule_upgrade(user_id: str, building_key: str, target_level: int, duration_secs: int):
    """Queue a new building‐upgrade for this user."""
    start_ts = int(datetime.utcnow().timestamp())
    append_row("Upgrades", [
        user_id,
        building_key,
        str(target_level),
        str(start_ts),
        str(duration_secs),
    ])

def complete_upgrades(user_id: str):
    """
    Remove any fully‐completed upgrades for this user,
    rewriting the sheet to keep only pending ones.
    """
    rows = get_rows(UPGRADES_RANGE)
    if len(rows) < 2:
        return
    now = int(datetime.utcnow().timestamp())
    data_rows = rows[1:]
    remaining = []

    for row in data_rows:
        if len(row) < 5:
            remaining.append(row)
            continue
        uid, key, lvl, start_ts, duration = row
        start_ts = int(start_ts); duration = int(duration)
        # omit only those for this user that are finished
        if not (uid == user_id and now >= start_ts + duration):
            remaining.append(row)

    # wipe & rewrite
    clear_range("Upgrades")
    append_row("Upgrades", HEADER_ROW)
    for r in remaining:
        append_row("Upgrades", r)

def get_pending_upgrades(user_id: str) -> list[tuple[str,int]]:
    """
    Return list of (building_key, remaining_seconds)
    for this user's in‐flight upgrades.
    """
    rows = get_rows(UPGRADES_RANGE)
    if len(rows) < 2:
        return []
    now = int(datetime.utcnow().timestamp())
    pending = []

    for row in rows[1:]:
        if len(row) < 5:
            continue
        uid, key, lvl, start_ts, duration = row
        if uid != user_id:
            continue
        start_ts = int(start_ts); duration = int(duration)
        rem = max(0, (start_ts + duration) - now)
        pending.append((key, rem))

    return pending
