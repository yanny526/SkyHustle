# sheets_service.py

import time
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
    'Leaderboard'
]

# Default headers for each sheet
_HEADERS = {
    'Players':     ['user_id', 'commander_name', 'telegram_username', 'credits', 'minerals', 'energy', 'last_seen'],
    'Buildings':   ['user_id', 'building_type', 'level', 'upgrade_end_ts'],
    'Army':        ['user_id', 'unit_type', 'count'],
    'CombatLog':   ['attacker_id', 'defender_id', 'timestamp', 'result', 'spoils_credits'],
    'Leaderboard': ['user_id', 'total_power', 'rank'],
}

def init():
    """
    Ensure the spreadsheet has all required sheets and headers.
    Call this once at bot startup.
    """
    # Fetch existing sheets
    spreadsheet = _service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing_titles = {s['properties']['title'] for s in spreadsheet.get('sheets', [])}

    # Prepare addSheet requests for missing tabs
    requests = []
    for title in REQUIRED_SHEETS:
        if title not in existing_titles:
            requests.append({'addSheet': {'properties': {'title': title}}})

    # Create missing sheets in one batch
    if requests:
        _service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': requests}
        ).execute()

    # Ensure each sheet has the correct header row
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

def get_rows(sheet_name: str) -> list:
    """
    Return all rows (as lists) from the given sheet.
    Row 0 is the header.
    """
    resp = _service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=sheet_name
    ).execute()
    return resp.get('values', [])

def append_row(sheet_name: str, values: list):
    """
    Append a single row of `values` to the bottom of `sheet_name`.
    """
    _service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=sheet_name,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [values]}
    ).execute()

def update_row(sheet_name: str, row_index: int, values: list):
    """
    Overwrite the row at zero-based `row_index` in `sheet_name` with `values`.
    """
    # Convert zero-based index to A1 notation (1-based)
    a1 = f"{sheet_name}!A{row_index + 1}"
    _service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=a1,
        valueInputOption='RAW',
        body={'values': [values]}
    ).execute()
