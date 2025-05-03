# sheets_service.py

import time
import os
from config import SERVICE_ACCOUNT_INFO, SHEET_ID
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
_creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
_service = build('sheets', 'v4', credentials=_creds)

# The tabs we need
REQUIRED_SHEETS = [
    'Players',
    'Buildings',
    'Army',
    'CombatLog',
    'Leaderboard',
    'Upgrades',              # ← newly added
]

# Default headers for each sheet
_HEADERS = {
    'Players':     ['user_id', 'commander_name', 'telegram_username', 'credits', 'minerals', 'energy', 'last_seen'],
    'Buildings':   ['user_id', 'building_type', 'level', 'upgrade_end_ts'],
    'Army':        ['user_id', 'unit_type', 'count'],
    'CombatLog':   ['attacker_id', 'defender_id', 'timestamp', 'result', 'spoils_credits'],
    'Leaderboard': ['user_id', 'total_power', 'rank'],
    'Upgrades':    ['user_id', 'building_type', 'start_ts', 'end_ts', 'target_level'],  # ← newly added
}

# Ensure all sheets exist and have the right header row
def init():
    # 1) Create any missing sheets
    requests = []
    existing = _service.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])
    existing_titles = {s['properties']['title'] for s in existing}

    for title in REQUIRED_SHEETS:
        if title not in existing_titles:
            requests.append({
                'addSheet': { 'properties': { 'title': title } }
            })

    if requests:
        _service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': requests}
        ).execute()

    # 2) Ensure each sheet has the correct header row
    for title, header in _HEADERS.items():
        _ensure_header_row(title, header)

def _ensure_header_row(sheet_name: str, header: list):
    """
    Check the first row of `sheet_name`; if it doesn't match `header`, overwrite it.
    """
    range_name = f"{sheet_name}!1:1"
    result = _service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=range_name
    ).execute()
    existing = result.get('values', [])
    if not existing or existing[0] != header:
        _service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body={'values': [header]}
        ).execute()

def get_rows(sheet_name: str) -> list[list[str]]:
    """
    Return all rows (as lists) from the given sheet, including the header.
    """
    # slight pause in case the sheet was just modified
    time.sleep(0.5)
    # read everything from column A through Z (adjust if you have more columns)
    range_name = f"{sheet_name}!A1:Z"
    resp = _service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=range_name
    ).execute()
    return resp.get('values', [])

def clear_sheet(sheet_name: str):
    """
    Remove all rows below the header in `sheet_name`.
    """
    # fetch how many rows exist
    rows = get_rows(sheet_name)
    if len(rows) <= 1:
        return
    # clear A2:Z (all data rows)
    _service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A2:Z"
    ).execute()

def append_row(sheet_name: str, values: list):
    """
    Append a single row of `values` to the bottom of `sheet_name`.
    """
    _service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A:Z",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [values]}
    ).execute()

def update_row(sheet_name: str, row_index: int, values: list):
    """
    Overwrite the row at zero-based `row_index` in `sheet_name` with `values`.
    """
    # Convert zero-based index to A1 notation (1-based)
    a1 = f"{sheet_name}!A{row_index + 1}:Z{row_index + 1}"
    _service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=a1,
        valueInputOption='RAW',
        body={'values': [values]}
    ).execute()

# Initialize on import
init()
