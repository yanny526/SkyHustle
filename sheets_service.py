# sheets_service.py

import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import SERVICE_ACCOUNT_INFO, SHEET_ID

# Scope for full read/write access
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Initialize credentials & Sheets API client once
_creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
_sheets = build("sheets", "v4", credentials=_creds).spreadsheets()


def get_rows(sheet_name: str) -> list[list[str]]:
    """
    Fetch all rows from the given sheet/tab.
    Returns a list of rows, each row is a list of cell values (strings).
    """
    try:
        # Specify a column range (A:Z) so the API can parse it
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
    Overwrite a particular row (row_index is zero-based) in sheet_name.
    """
    try:
        # Google Sheets rows are 1-based
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
    """
    try:
        body = {"values": [row_values]}
        # Again, include a column range so the API can parse the request
        _sheets.values().append(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!A:Z",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
    except Exception as e:
        logging.error(f"[sheets_service] append_row({sheet_name!r}) failed: {e}")
