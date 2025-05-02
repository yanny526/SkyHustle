import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Load service‐account JSON from env var
SERVICE_ACCOUNT_INFO = json.loads(
    os.getenv("BASE64_CREDS")
    or os.getenv("SERVICE_ACCOUNT_INFO", "{}")
)
SHEET_ID = os.getenv("SHEET_ID")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)

def get_service():
    return build("sheets", "v4", credentials=creds)

def get_rows(range_name: str) -> list[list[str]]:
    resp = get_service().spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=range_name
    ).execute()
    return resp.get("values", [])

def append_row(range_name: str, values: list[str]):
    return get_service().spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [values]}
    ).execute()

def clear_range(range_name: str):
    return get_service().spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range=range_name
    ).execute()


# ——— Default headers for each tab ———
DEFAULT_HEADERS = {
    "Players":   ["user_id", "player_name", "created_ts"],
    "Buildings": ["user_id", "building_key", "level", "last_updated_ts"],
    "Resources": ["user_id", "resource_key", "amount", "prod_per_hour"],
    "Upgrades":  ["user_id", "building_key", "target_level", "start_ts", "duration_secs"],
    "Queue":     ["user_id", "action", "start_ts", "duration_secs"],
}

def init_sheets():
    """
    On bot startup, ensure each sheet tab has its header row.
    """
    for tab, header in DEFAULT_HEADERS.items():
        existing = get_rows(f"{tab}!A1:1")
        if not existing or existing[0] != header:
            clear_range(tab)
            append_row(tab, header)
