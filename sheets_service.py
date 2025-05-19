# sheets_service.py

import time
import os
import logging
from config import SERVICE_ACCOUNT_INFO, SHEET_ID
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# ─── Google Sheets API setup ─────────────────────────────────────────────────

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
_creds   = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
_service = build('sheets', 'v4', credentials=_creds)

# ─── Core tabs your game needs (for init check) ───────────────────────────────
REQUIRED_SHEETS = [
    'Players',
    'BuildingDefs',
    'BuildQueue',
    'CompletedBuilds',
    'Army',
    'CombatLog',
    'Leaderboard',
    'Upgrades',
    # add any other tabs you refer to…
]

# ─── Default header row for each tab ───────────────────────────────────────────
_HEADERS: dict[str, list[str]] = {
    'Players':        ['user_id','commander_name','telegram_username','credits','minerals','energy','last_seen','progress'],
    'BuildingDefs':   ['key','name','tier','cost_c','cost_m','cost_e','time_sec','slots_required','prereqs'],
    'BuildQueue':     ['user_id','building','to_level','start_ts','end_ts'],
    'CompletedBuilds':['user_id','building','level','completed_ts'],
    'Army':           ['user_id','unit_type','count'],
    'CombatLog':      ['attacker_id','defender_id','timestamp','result','spoils_credits'],
    'Leaderboard':    ['user_id','total_power','rank'],
    'Upgrades':       ['user_id','building_type','start_ts','end_ts','target_level'],
}

def init():
    """
    Ensure all REQUIRED_SHEETS exist and have the correct header row.
    Call once at startup (your main.py → sheets_init()).
    """
    # 1) Create any missing sheets
    try:
        resp = _service.spreadsheets()\
            .get(spreadsheetId=SHEET_ID, fields='sheets.properties.title')\
            .execute()
        existing = {s['properties']['title'] for s in resp.get('sheets', [])}
    except HttpError as e:
        logger.error("sheets_service.init: cannot fetch spreadsheet: %s", e)
        return

    requests = []
    for title in REQUIRED_SHEETS:
        if title not in existing:
            requests.append({'addSheet':{'properties':{'title':title}}})
    if requests:
        try:
            _service.spreadsheets()\
                .batchUpdate(spreadsheetId=SHEET_ID, body={'requests':requests})\
                .execute()
        except HttpError as e:
            logger.error("sheets_service.init: cannot create sheets: %s", e)
            return

    # 2) Ensure correct headers
    for sheet, header in _HEADERS.items():
        _ensure_header_row(sheet, header)

def _ensure_header_row(sheet_name: str, header: list[str]):
    """If row 1 doesn’t match, overwrite it."""
    try:
        result = _service.spreadsheets().values()\
            .get(spreadsheetId=SHEET_ID, range=f"{sheet_name}!1:1")\
            .execute()
        existing = result.get('values', [])
        if not existing or existing[0] != header:
            _service.spreadsheets().values()\
                .update(
                    spreadsheetId=SHEET_ID,
                    range=f"{sheet_name}!1:1",
                    valueInputOption='RAW',
                    body={'values':[header]}
                ).execute()
    except HttpError as e:
        logger.error("sheets_service._ensure_header_row(%s): %s", sheet_name, e)

def get_rows(sheet_name: str) -> list[list[str]]:
    """
    Return all rows (including header) from the given sheet.
    """
    try:
        # guard eventual consistency
        time.sleep(0.5)
        resp = _service.spreadsheets().values()\
            .get(spreadsheetId=SHEET_ID, range=f"{sheet_name}!A1:Z")\
            .execute()
        return resp.get('values', [])
    except HttpError as e:
        logger.error("sheets_service.get_rows(%s): %s", sheet_name, e)
        return []

def update_row(sheet_name: str, row_index: int, values: list[str]):
    """
    Overwrite row at zero-based `row_index` (A=0) in `sheet_name` with `values`.
    """
    try:
        a1 = f"{sheet_name}!A{row_index+1}:Z{row_index+1}"
        _service.spreadsheets().values()\
            .update(
                spreadsheetId=SHEET_ID,
                range=a1,
                valueInputOption='RAW',
                body={'values':[values]}
            ).execute()
    except HttpError as e:
        logger.error("sheets_service.update_row(%s,%d): %s", sheet_name, row_index, e)

def append_row(sheet_name: str, values: list[str]):
    """
    Append a single row of `values` to the bottom of `sheet_name`.
    """
    try:
        _service.spreadsheets().values()\
            .append(
                spreadsheetId=SHEET_ID,
                range=f"{sheet_name}!A1:Z",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values':[values]}
            ).execute()
    except HttpError as e:
        logger.error("sheets_service.append_row(%s): %s", sheet_name, e)

def clear_sheet(sheet_name: str):
    """Delete all data below the header in `sheet_name`."""
    try:
        _service.spreadsheets().values()\
            .clear(spreadsheetId=SHEET_ID, range=f"{sheet_name}!A2:Z")\
            .execute()
    except HttpError as e:
        logger.error("sheets_service.clear_sheet(%s): %s", sheet_name, e)

def ensure_sheet(tab_name: str, header: list[str]):
    """
    Auto-create a single tab with the given header if it does not exist.
    """
    try:
        meta   = _service.spreadsheets().get(
            spreadsheetId=SHEET_ID, fields="sheets.properties.title"
        ).execute()
        titles = [s["properties"]["title"] for s in meta.get("sheets",[])]
        if tab_name not in titles:
            _service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={"requests":[{"addSheet":{"properties":{"title":tab_name}}}]}
            ).execute()
            append_row(tab_name, header)
    except HttpError as e:
        logger.error("sheets_service.ensure_sheet(%s): %s", tab_name, e)
