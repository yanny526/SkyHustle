from sheets_service import get_rows, append_row, update_row
from datetime import datetime

WHISPER_SHEET = "Whispers"
MAX_RECORDS = 5

def record_whisper(sender_id: str, recipient_id: str, message: str):
    """
    Append a whisper to the Whispers sheet and prune to keep only the last MAX_RECORDS entries.
    """
    # 1) Append new record
    timestamp = datetime.utcnow().isoformat()
    append_row(WHISPER_SHEET, [sender_id, recipient_id, timestamp, message])

    # 2) Prune old records
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
    Returns a list of tuples (sender_id, recipient_id, timestamp, message).
    """
    rows = get_rows(WHISPER_SHEET)[1:]
    msgs = []
    for row in rows:
        if len(row) < 4:
            continue
        s, r, ts, msg = row
        if s == uid or r == uid:
            msgs.append((s, r, ts, msg))
    # Sort by timestamp
    msgs.sort(key=lambda x: x[2])
    return msgs[-limit:]
