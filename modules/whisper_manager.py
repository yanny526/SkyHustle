from sheets_service import get_rows, append_row, update_row
from datetime import datetime

WHISPER_SHEET = "Whispers"
MAX_RECORDS = 5


def record_whisper(sender_id: str, recipient_id: str, message: str):
    """
    Append a whisper to the Whispers sheet (including sender's game name) and prune to keep only the last MAX_RECORDS entries.
    """
    # 1) Lookup game names
    players = get_rows("Players")[1:]
    id_to_name = {r[0]: (r[1] or "Unknown") for r in players}
    sender_name = id_to_name.get(sender_id, "Unknown")
    recipient_name = id_to_name.get(recipient_id, "Unknown")

    # 2) Append new record with extra name fields
    timestamp = datetime.utcnow().isoformat()
    append_row(WHISPER_SHEET, [sender_id, sender_name, recipient_id, recipient_name, timestamp, message])

    # 3) Prune old records
    rows = get_rows(WHISPER_SHEET)
    header, data = rows[0], rows[1:]
    total = len(data)
    if total <= MAX_RECORDS:
        return

    # Keep only the last MAX_RECORDS entries
    keep = data[-MAX_RECORDS:]

    # Overwrite sheet rows 2..MAX_RECORDS+1 with the kept entries
    for idx, row in enumerate(keep, start=1):
        update_row(WHISPER_SHEET, idx, row)

    # Clear any leftover rows beyond the kept entries
    blank = [""] * len(header)
    for idx in range(MAX_RECORDS + 1, total + 1):
        update_row(WHISPER_SHEET, idx, blank)


def fetch_recent_whispers(uid: str, limit: int = MAX_RECORDS):
    """
    Fetch up to `limit` most recent whispers sent or received by `uid`.
    Returns a list of tuples (sender_id, sender_name, recipient_id, recipient_name, timestamp, message).
    """
    rows = get_rows(WHISPER_SHEET)[1:]
    msgs = []
    for row in rows:
        if len(row) < 6:
            continue
        s_id, s_name, r_id, r_name, ts, msg = row
        if s_id == uid or r_id == uid:
            msgs.append((s_id, s_name, r_id, r_name, ts, msg))
    # Sort by timestamp
    msgs.sort(key=lambda x: x[4])
    return msgs[-limit:]
