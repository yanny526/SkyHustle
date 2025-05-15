# sheets_service.py

import os
import time
import threading
import logging
from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ─── Configuration ───────────────────────────────────────────────────────────
LOG = logging.getLogger(__name__)
LOG_LEVEL = os.getenv("SHEETS_LOG_LEVEL", "INFO").upper()
LOG.setLevel(LOG_LEVEL)

SCOPES         = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
CREDS_JSON     = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # path to service account JSON
CACHE_TTL      = int(os.getenv("SHEETS_CACHE_TTL_SEC", 30))   # seconds to cache reads

# ─── Required tabs and their headers ──────────────────────────────────────────
REQUIRED_SHEETS = {
    'Players':     ['user_id', 'commander_name', 'telegram_username', 'credits', 'minerals', 'energy', 'last_seen'],
    'Buildings':   ['user_id', 'building_type', 'level', 'upgrade_end_ts'],
    'Army':        ['user_id', 'unit_type', 'count'],
    'CombatLog':   ['attacker_id', 'defender_id', 'timestamp', 'result', 'spoils_credits'],
    'Leaderboard': ['user_id', 'total_power', 'rank'],
    'Upgrades':    ['user_id', 'building_type', 'start_ts', 'end_ts', 'target_level'],
}

# ─── Internal state ───────────────────────────────────────────────────────────
_service     = None
_service_lock = threading.Lock()

_row_cache   = {}   # sheet_name -> (timestamp, rows)
_cache_lock  = threading.Lock()

# ─── Sheets API client setup ──────────────────────────────────────────────────
def _get_service():
    global _service
    with _service_lock:
        if _service is None:
            creds = Credentials.from_service_account_file(CREDS_JSON, scopes=SCOPES)
            _service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        return _service

# ─── Initialization: create tabs & headers ────────────────────────────────────
def init():
    """Ensure all REQUIRED_SHEETS exist and have correct header rows."""
    svc = _get_service()
    try:
        meta = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields="sheets.properties.title").execute()
        existing = {s["properties"]["title"] for s in meta.get("sheets", [])}
        requests = []
        for title in REQUIRED_SHEETS:
            if title not in existing:
                LOG.info("Creating missing sheet tab: %s", title)
                requests.append({"addSheet": {"properties": {"title": title}}})
        if requests:
            svc.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"requests": requests}
            ).execute()

        # enforce headers
        for title, header in REQUIRED_SHEETS.items():
            _ensure_header_row(svc, title, header)
    except HttpError as e:
        LOG.error("Failed to initialize sheets: %s", e)
        raise

def _ensure_header_row(svc, sheet_name: str, header: List[str]):
    """Overwrite first row if it doesn’t match the expected header."""
    rng = f"{sheet_name}!1:1"
    try:
        resp = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=rng).execute()
        existing = resp.get("values", [])
        if not existing or existing[0] != header:
            LOG.info("Setting header for %s → %s", sheet_name, header)
            svc.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=rng,
                valueInputOption="RAW",
                body={"values": [header]},
            ).execute()
    except HttpError as e:
        LOG.error("Error ensuring header for %s: %s", sheet_name, e)
        raise

# ─── Core I/O with caching ─────────────────────────────────────────────────────
def get_rows(sheet_name: str) -> List[List[str]]:
    """
    Return all rows (including header) from `sheet_name`, caching for CACHE_TTL seconds.
    """
    now = time.time()
    with _cache_lock:
        ts_rows = _row_cache.get(sheet_name)
        if ts_rows and now - ts_rows[0] < CACHE_TTL:
            return ts_rows[1]

    # cache miss or expired
    svc = _get_service()
    rng = f"{sheet_name}!A1:Z"
    try:
        resp = svc.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=rng
        ).execute()
        rows = resp.get("values", [])
    except HttpError as e:
        LOG.error("Error reading sheet %s: %s", sheet_name, e)
        rows = []

    with _cache_lock:
        _row_cache[sheet_name] = (now, rows)
    return rows

def append_row(sheet_name: str, values: List[str]):
    """
    Append a single row to `sheet_name`, and invalidate its cache.
    """
    svc = _get_service()
    rng = f"{sheet_name}!A1:Z"
    try:
        svc.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=rng,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [values]},
        ).execute()
    except HttpError as e:
        LOG.error("Error appending row to %s: %s", sheet_name, e)
        raise
    finally:
        _invalidate_cache(sheet_name)

def update_row(sheet_name: str, row_index: int, values: List[str]):
    """
    Overwrite the row at zero-based `row_index` (including header) in `sheet_name`.
    """
    svc = _get_service()
    # +1 because A1 notation is 1-based
    a1 = f"{sheet_name}!A{row_index+1}:Z{row_index+1}"
    try:
        svc.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=a1,
            valueInputOption="RAW",
            body={"values": [values]},
        ).execute()
    except HttpError as e:
        LOG.error("Error updating row %d in %s: %s", row_index, sheet_name, e)
        raise
    finally:
        _invalidate_cache(sheet_name)

def clear_sheet(sheet_name: str):
    """
    Delete all data below the header in `sheet_name`.
    """
    svc = _get_service()
    rng = f"{sheet_name}!A2:Z"
    try:
        svc.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=rng
        ).execute()
    except HttpError as e:
        LOG.error("Error clearing sheet %s: %s", sheet_name, e)
        raise
    finally:
        _invalidate_cache(sheet_name)

def _invalidate_cache(sheet_name: str):
    """Internal: drop any cached rows for this sheet."""
    with _cache_lock:
        _row_cache.pop(sheet_name, None)

