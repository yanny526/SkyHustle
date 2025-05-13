# modules/admin_manager.py

from sheets_service import get_rows

def get_admin_ids() -> set[str]:
    """
    Reads the 'Administrators' sheet and returns a set of user_id strings
    who are allowed to run admin commands.
    """
    rows = get_rows("Administrators")
    # assume first row is header
    return {r[0] for r in rows[1:] if r}

def is_admin(uid: str) -> bool:
    """
    Returns True if uid (string) is listed in the Administrators sheet.
    """
    return uid in get_admin_ids()
