import os, json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# load your service account and sheet ID from env
SERVICE_ACCOUNT_INFO = json.loads(os.getenv("SERVICE_ACCOUNT_INFO") or "{}")
SHEET_ID             = os.getenv("SHEET_ID")
SCOPES               = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

def init():
    """
    Create missing sheets & headers if they don’t already exist.
    Call this once at bot startup.
    """
    ss = service.spreadsheets()
    meta = ss.get(spreadsheetId=SHEET_ID).execute()
    existing = {s["properties"]["title"] for s in meta["sheets"]}

    # define all the tabs you need and their headers
    tabs = {
        "Players":    ["user_id", "username", "minerals", "credits", "infantry", "tanks", "artillery"],
        "Upgrades":   ["user_id", "what", "started_at", "done_at"],
        "Queue":      ["user_id", "unit", "qty", "started_at", "done_at"],
        "Leaderboard":["user_id","username","score"],
        # add other tabs here…
    }

    requests = []
    for name, headers in tabs.items():
        if name not in existing:
            # add sheet
            requests.append({
                "addSheet": {"properties": {"title": name}}
            })
        # set headers row
        requests.append({
            "updateCells": {
                "start": {"sheetId": None, "rowIndex": 0, "columnIndex": 0},
                "rows": [{"values":[{"userEnteredValue":{"stringValue":h}} for h in headers]}],
                "fields": "userEnteredValue"
            }
        })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={"requests": requests}
        ).execute()

def get_rows(sheet_name: str, range_: str = None):
    rng = f"{sheet_name}!{range_}" if range_ else sheet_name
    resp = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=rng
    ).execute()
    return resp.get("values", [])

def append_row(sheet_name: str, row: list):
    body = {"values":[row]}
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=sheet_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

def update_row(sheet_name: str, row: list, row_index: int):
    body = {"values":[row]}
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A{row_index}:Z{row_index}",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
