# skyhustle-main/sheets_service.py

import os
import base64
import json

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 1) Load & parse your service‐account credentials from an env var
BASE64_CREDS = os.getenv("BASE64_CREDS")
if not BASE64_CREDS:
    raise RuntimeError("Missing environment variable: BASE64_CREDS")

try:
    SERVICE_ACCOUNT_INFO = json.loads(base64.b64decode(BASE64_CREDS))
except Exception as e:
    raise RuntimeError("Could not decode BASE64_CREDS: " + str(e))

SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("Missing environment variable: SHEET_ID")

# 2) Build the Sheets API client
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES,
)
service = build("sheets", "v4", credentials=creds)

# 3) Define the sheets you need and their header rows
DEFAULT_HEADERS = {
    "Players":       ["user_id", "username", "credits", "minerals", "energy", "last_update"],
    "Upgrades":      ["user_id", "upgrade", "level", "start_ts", "end_ts"],
    "Units":         ["user_id", "Infantry", "Tanks", "Artillery",
                      "HeavyInfantry", "AssaultTank", "RocketLauncher",
                      "BattleTank", "MechInfantry", "SiegeCannon"],
    # add any additional tabs & headers here...
}

def init_sheets():
    """
    Ensure that each tab in DEFAULT_HEADERS exists, and that its first row
    is set to the header list.
    """
    # Fetch existing sheet names
    spread = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {sheet["properties"]["title"] for sheet in spread.get("sheets", [])}

    # Create any missing sheets
    requests = []
    for title in DEFAULT_HEADERS:
        if title not in existing:
            requests.append({"addSheet": {"properties": {"title": title}}})
    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": requests}
        ).execute()

    # Write headers into row 1 of each sheet
    for title, headers in DEFAULT_HEADERS.items():
        end_col = chr(ord("A") + len(headers) - 1)
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"{title}!A1:{end_col}1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

def get_rows(sheet_name: str) -> list[list[str]]:
    """Return all rows (including header) from a given sheet/tab."""
    resp = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=sheet_name,
    ).execute()
    return resp.get("values", [])

def append_row(sheet_name: str, row: list) -> None:
    """Append a single row to the bottom of the given sheet/tab."""
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=sheet_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()

def clear_range(sheet_name: str, cell_range: str = "A2:Z") -> None:
    """
    Clear out cells in the given sheet from row 2 down through Z (by default).
    Pass a different range if you need a different block.
    """
    service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!{cell_range}",
        body={},
    ).execute()
