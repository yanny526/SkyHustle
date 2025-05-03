from sheets_service import get_rows, update_row


def complete_upgrades(user_id):
    """
    Scan the ‘Upgrades’ sheet and mark any in-progress upgrades
    for this user as completed once their time has elapsed.
    """
    all_rows = get_rows("Upgrades")
    if not all_rows or len(all_rows) < 2:
        return  # nothing to do if there’s no data

    header, *data_rows = all_rows

    for idx, row in enumerate(data_rows, start=2):
        # Expect at least 4 columns: user_id, upgrade_id, target_building, status
        if len(row) < 4:
            continue

        row_user, upgrade_id, target, status = row[:4]
        if row_user == str(user_id) and status == "in_progress":
            # Here you could check timestamps, etc. before completing.
            # For now, we simply mark it completed:
            updated = [row_user, upgrade_id, target, "completed"]
            update_row("Upgrades", idx, updated)


def get_pending_upgrades(user_id):
    """
    Return a list of this user’s upgrades that are still in_progress.
    """
    all_rows = get_rows("Upgrades")
    if not all_rows or len(all_rows) < 2:
        return []

    header, *data_rows = all_rows
    pending = []

    for row in data_rows:
        if len(row) < 4:
            continue
        row_user, upgrade_id, target, status = row[:4]
        if row_user == str(user_id) and status == "in_progress":
            pending.append({
                "upgrade_id": upgrade_id,
                "building": target,
                "status": status
            })

    return pending
