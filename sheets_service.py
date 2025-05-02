from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import SERVICE_ACCOUNT_INFO, SHEET_ID
import time

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

REQUIRED_SHEETS = ['Players', 'Buildings', 'Army', 'CombatLog', 'Leaderboard']

def init():
    # Ensure each sheet exists
    ss = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = [s['properties']['title'] for s in ss.get('sheets', [])]
    requests = []
    for name in REQUIRED_SHEETS:
        if name not in existing:
            requests.append({'addSheet': {'properties': {'title': name}}})
    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': requests}
        ).execute()

def get_rows(sheet):
    res = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=sheet).execute()
    return res.get('values', [])

def append_row(sheet, row):
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=sheet,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [row]}
    ).execute()

def update_row(sheet, row_index, values):
    range_str = f"{sheet}!A{row_index + 1}"
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=range_str,
        valueInputOption='RAW',
        body={'values': [values]}
    ).execute()

# Additional helper functions would go here...
