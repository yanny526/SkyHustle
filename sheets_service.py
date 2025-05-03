import os
import base64
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

from config import BASE64_CREDS, SHEET_ID

# Decode and build credentials
SERVICE_ACCOUNT_INFO = json.loads(base64.b64decode(BASE64_CREDS).decode())
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
_service = build("sheets", "v4", credentials=_creds)

def get_rows(tab_name: str) -> list[list[str]]:
    """
    Read all values from the given sheet/tab.
    Returns a list of rows, each row is a list of cell strings.
    """
    range_name = f"{tab_name}!A1:Z"
    try:
        result = _service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=range_name
        ).execute()
        return result.get("values", [])
    except HttpError:
        # Propagate to caller
        raise

def update_row(tab_name: str, idx: int, row: list[str]):
    """
    Overwrite row at zero-based index `idx` (plus header) with the given list.
    """
    range_name = f"{tab_name}!A{idx+1}:Z{idx+1}"
    _service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [row]}
    ).execute()

def append_row(tab_name: str, row: list[str]):
    """
    Append a single new row to the bottom of the sheet.
    """
    _service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{tab_name}!A1:Z",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]}
    ).execute()

def clear_sheet(tab_name: str):
    """
    Delete all data below the header in the sheet.
    """
    _service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range=f"{tab_name}!A2:Z"
    ).execute()

def ensure_sheet(tab_name: str, header: list[str]):
    """
    Ensure that a sheet/tab named `tab_name` exists.
    If missing, create it and write the provided header as row 1.
    """
    meta = _service.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        fields="sheets.properties.title"
    ).execute()
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]

    if tab_name not in titles:
        _service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={
                "requests": [
                    {"addSheet": {"properties": {"title": tab_name}}}
                ]
            }
        ).execute()
        append_row(tab_name, header)
