# modules/chaos_storms_manager.py

import random
import time
from sheets_service import get_rows, update_row, append_row

# Define each storm: 2 beneficial, 3 destructive
EVENTS = [
    {
        "id": "solar_surge",
        "title": "Solar Surge",
        "emoji": "🌞",
        "story": "A cosmic flare empowers your reactors! Everyone gains +200 Energy.",
        "apply": lambda _: ("energy", +200),
    },
    {
        "id": "meteoric_orefall",
        "title": "Meteoric Orefall",
        "emoji": "🌋",
        "story": "Rare meteoric ore rains down! Everyone gains +150 Minerals.",
        "apply": lambda _: ("minerals", +150),
    },
    {
        "id": "credit_crash",
        "title": "Credit Crash",
        "emoji": "💸",
        "story": "A global market meltdown! Everyone loses 200 Credits.",
        "apply": lambda _: ("credits", -200),
    },
    {
        "id": "mineral_drought",
        "title": "Mineral Drought",
        "emoji": "⛏️",
        "story": "Veins run dry across the world! Everyone loses 150 Minerals.",
        "apply": lambda _: ("minerals", -150),
    },
    {
        "id": "power_blackout",
        "title": "Power Blackout",
        "emoji": "⚡",
        "story": "An EMP wave knocks out grids! Everyone loses 100 Energy.",
        "apply": lambda _: ("energy", -100),
    },
]

LOG_SHEET = "ChaosStormsLog"

def pick_random_storm():
    return random.choice(EVENTS)

def apply_storm_to_all(storm):
    """
    Apply the chosen storm to every player, update their sheet row,
    then log the occurrence in ChaosStormsLog.
    Returns (storm, delta) so callers can report what happened.
    """
    players = get_rows("Players")
    header, data = players[0], players[1:]
    col_idx = {col: i for i, col in enumerate(header)}
    field, delta = storm["apply"](None)

    # 1) update each player’s resource
    for row_i, row in enumerate(data, start=1):
        old = int(row[col_idx[field]])
        new = max(0, old + delta)
        row[col_idx[field]] = str(new)
        update_row("Players", row_i, row)

    # 2) log the storm
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    append_row(LOG_SHEET, [ts, storm["id"], storm["title"], storm["story"]])

    return storm, delta
