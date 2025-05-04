from sheets_service import get_rows

def get_admin_ids():
    rows = get_rows("Administrators")
    return {r[0] for r in rows[1:]}

def is_admin(uid: str):
    return uid in get_admin_ids()
