```python
# modules/chaos_storms_manager.py

import random
from datetime import datetime, timedelta
from sheets_service import get_rows, append_row, update_row
from googleapiclient.errors import HttpError

LOG_SHEET = "ChaosLog"
LOG_HEADER = ["storm_id", "timestamp"]

# Define five Chaos Storms (3 destructive, 2 beneficial)
STORMS = [
    {
        "id": "ember_rain",
        "name": "Ember Rain",
        "emoji": "🌋",
        "story": (
            "Dark ember rain scorches your mineral caches,\n"
            "burning away 100 Minerals from every commander."
        ),
        "delta": {"minerals": -100},
    },
    {
        "id": "silver_gale",
        "name": "Silver Gale",
        "emoji": "🍃",
        "story": (
            "A refreshing silver gale revitalizes everyone’s energy,\n"
            "granting +150 Energy to all."
        ),
        "delta": {"energy": +150},
    },
    {
        "id": "ruinsquake",
        "name": "Ruinsquake",
        "emoji": "🏚️",
        "story": (
            "Tremors shake your base foundations,\n"
            "costing 100 Credits from each commander."
        ),
        "delta": {"credits": -100},
    },
    {
        "id": "golden_sunrise",
        "name": "Golden Sunrise",
        "emoji": "🌅",
        "story": (
            "A golden sunrise bathes the land,\n"
            "bestowing +200 Minerals to every commander."
        ),
        "delta": {"minerals": +200},
    },
    {
        "id": "voidstorm",
        "name": "Voidstorm",
        "emoji": "🌀",
        "story": (
            "An unnatural voidstorm rips through,\n"
            "siphoning 50 Energy and 50 Credits from all."
        ),
        "delta": {"energy": -50, "credits": -50},
    },
]


def _ensure_log_sheet():
    """
    Ensure the ChaosLog sheet exists with the correct header.
    """
    try:
        rows = get_rows(LOG_SHEET)
    except HttpError:
        rows = []
    if not rows or rows[0] != LOG_HEADER:
        append_row(LOG_SHEET, LOG_HEADER)


def _last_storm_time():
    """
    Return the datetime of the last recorded storm, or None if not available.
    """
    try:
        rows = get_rows(LOG_SHEET)[1:]
    except HttpError:
        return None
    if not rows:
        return None
    ts = rows[-1][1]
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def can_trigger():
    """
    Return True if at least 7 days have passed since the last storm.
    """
    _ensure_log_sheet()
    last = _last_storm_time()
    if not last:
        return True
    return datetime.utcnow() - last >= timedelta(days=7)


def record_storm(storm_id: str):
    """
    Record a new storm occurrence in the log sheet.
    """
    now = datetime.utcnow().isoformat()
    append_row(LOG_SHEET, [storm_id, now])


def get_random_storm():
    """Pick one of the five storms at random."""
    return random.choice(STORMS)


def apply_storm(storm):
    """
    Apply the storm's resource changes to every player.
    """
    players = get_rows("Players")
    for idx, row in enumerate(players[1:], start=1):
        c = int(row[3])
        m = int(row[4])
        e = int(row[5])
        d = storm["delta"]
        c = max(0, c + d.get("credits", 0))
        m = max(0, m + d.get("minerals", 0))
        e = max(0, e + d.get("energy", 0))
        row[3], row[4], row[5] = str(c), str(m), str(e)
        update_row("Players", idx, row)


def trigger_storm():
    """
    If enough time has passed, pick & apply a new storm,
    record it, and return the storm dict. Otherwise, return None.
    """
    if not can_trigger():
        return None
    storm = get_random_storm()
    apply_storm(storm)
    record_storm(storm["id"])
    return storm
```
