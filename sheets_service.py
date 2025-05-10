# sheets_service.py

import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import SERVICE_ACCOUNT_INFO, SHEET_ID

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Initialize credentials & Sheets API client once
_creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
_sheets = build("sheets", "v4", credentials=_creds).spreadsheets()

def ensure_sheet(sheet_name: str) -> None:
    """
    Creates a new sheet/tab with the given name if it does not already exist.
    """
    try:
        meta = _sheets.get(spreadsheetId=SHEET_ID).execute()
        titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
        if sheet_name not in titles:
            batch_req = {
                "requests": [
                    {"addSheet": {"properties": {"title": sheet_name}}}
                ]
            }
            _sheets.batchUpdate(
                spreadsheetId=SHEET_ID,
                body=batch_req
            ).execute()
            logging.info(f"[sheets_service] Created sheet: {sheet_name}")
    except Exception as e:
        logging.error(f"[sheets_service] ensure_sheet({sheet_name!r}) failed: {e}")

def get_rows(sheet_name: str) -> list[list[str]]:
    """
    Fetch all rows from the given sheet/tab.
    Auto-creates the tab if missing.
    """
    ensure_sheet(sheet_name)
    try:
        range_str = f"{sheet_name}!A:Z"
        resp = _sheets.values().get(
            spreadsheetId=SHEET_ID,
            range=range_str
        ).execute()
        return resp.get("values", [])
    except Exception as e:
        logging.error(f"[sheets_service] get_rows({sheet_name!r}) failed: {e}")
        return []

def update_row(sheet_name: str, row_index: int, row_values: list) -> None:
    """
    Overwrite a particular row (zero-based index) in sheet_name.
    Auto-creates the tab if missing.
    """
    ensure_sheet(sheet_name)
    try:
        range_str = f"{sheet_name}!A{row_index + 1}"
        body = {"values": [row_values]}
        _sheets.values().update(
            spreadsheetId=SHEET_ID,
            range=range_str,
            valueInputOption="RAW",
            body=body
        ).execute()
    except Exception as e:
        logging.error(f"[sheets_service] update_row({sheet_name!r}, {row_index}) failed: {e}")

def append_row(sheet_name: str, row_values: list) -> None:
    """
    Append a new row with `row_values` to the bottom of `sheet_name`.
    Auto-creates the tab if missing.
    """
    ensure_sheet(sheet_name)
    try:
        body = {"values": [row_values]}
        _sheets.values().append(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!A:Z",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
    except Exception as e:
        logging.error(f"[sheets_service] append_row({sheet_name!r}) failed: {e}")
