import logging
from sheets_service import get_rows, update_row

logger = logging.getLogger(__name__)

def complete_upgrades(user_id):
    """
    Scan the ‘Upgrades’ sheet and mark any in-progress upgrades
    for this user as completed once their time has elapsed.
    """
    all_rows = get_rows("Upgrades") or []
    # nothing to do if we have no data or only header
    if len(all_rows) < 2:
        return

    # Skip header row; sheet rows are 1-indexed so header is row 1
    for sheet_idx, row in enumerate(all_rows[1:], start=2):
        # Expect at least [user_id, upgrade_id, target, status]
        if len(row) < 4:
            logger.warning(f"Upgrades row {sheet_idx} too short, skipping: {row}")
            continue

        row_user, upgrade_id, target, status = row[:4]

        # only care about this user's in-progress upgrades
        if str(row_user) == str(user_id) and status == "in_progress":
            # TODO: pull timestamp (e.g. row[4]) and only complete if time has passed
            updated = row.copy()
            updated[3] = "completed"
            try:
                update_row("Upgrades", sheet_idx, updated)
                logger.info(f"Upgrade {upgrade_id} for user {user_id} marked completed.")
            except Exception as e:
                logger.error(f"Failed to update Upgrades row {sheet_idx}: {e}")

def get_pending_upgrades(user_id):
    """
    Return a list of this user’s upgrades still in progress.
    """
    all_rows = get_rows("Upgrades") or []
    if len(all_rows) < 2:
        return []

    pending = []
    for sheet_idx, row in enumerate(all_rows[1:], start=2):
        if len(row) < 4:
            logger.warning(f"Upgrades row {sheet_idx} too short, skipping: {row}")
            continue

        row_user, upgrade_id, target, status = row[:4]
        if str(row_user) == str(user_id) and status == "in_progress":
            pending.append({
                "upgrade_id": upgrade_id,
                "building": target,
                "status": status
            })

    return pending
