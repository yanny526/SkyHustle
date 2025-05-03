# modules/building_manager.py

from sheets_service import get_rows
from config import BUILDING_MAX_LEVEL

def get_building_info(user_id: str) -> dict:
    """
    Returns a dict mapping each building type to its current level for the given user.
    """
    rows = get_rows('Buildings')[1:]  # skip header
    info = {}
    for row in rows:
        if row[0] == user_id:
            btype = row[1]
            level = int(row[2])
            info[btype] = level

    # Ensure every known building type appears, defaulting to 0
    return {
        btype: info.get(btype, 0)
        for btype in BUILDING_MAX_LEVEL.keys()
    }
