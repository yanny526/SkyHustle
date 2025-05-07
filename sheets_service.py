# sheets_service.py

import time
import os
import base64
import json
from config import SERVICE_ACCOUNT_INFO, SHEET_ID
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
_creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
_service = build('sheets', 'v4', credentials=_creds)

REQUIRED_SHEETS = [
    'Players',
    'Buildings',
    'Army',
    'CombatLog',
    'Leaderboard',
    'Upgrades',
    'AI_Commanders',
    'AI_Army'
]

_HEADERS = {
    'Players': ['user_id', 'commander_name', 'telegram_username', 'credits', 'minerals', 'energy', 'last_seen', 'premium_credits'],
    'Buildings': ['user_id', 'building_type', 'level', 'upgrade_end_ts'],
    'Army': ['user_id', 'unit_type', 'count'],
    'CombatLog': ['attacker_id', 'defender_id', 'timestamp', 'result', 'spoils_credits'],
    'Leaderboard': ['user_id', 'total_power', 'rank'],
    'Upgrades': ['user_id', 'building_type', 'start_ts', 'end_ts', 'target_level'],
    'AI_Commanders': ['user_id', 'commander_name', 'credits', 'minerals', 'energy'],
    'AI_Army': ['ai_id', 'unit_type', 'count']
}

def init():
    resp = _service.spreadsheets().get(spreadsheetId=SHEET_ID, fields='sheets.properties.title').execute()
    existing = {s['properties']['title'] for s in resp.get('sheets', [])}

    requests = []
    for title in REQUIRED_SHEETS:
        if title not in existing:
            requests.append({'addSheet': {'properties': {'title': title}}})

    if requests:
        _service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': requests}
        ).execute()

    for sheet_name, header in _HEADERS.items():
        _ensure_header_row(sheet_name, header)

def _ensure_header_row(sheet_name: str, header: list[str]):
    range_name = f"{sheet_name}!1:1"
    try:
        result = _service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=range_name
        ).execute()
    except HttpError:
        result = {'values': []}
    existing = result.get('values', [])
    if not existing or existing[0] != header:
        _service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body={'values': [header]}
        ).execute()

def get_rows(sheet_name: str) -> list[list[str]]:
    time.sleep(0.5)
    range_name = f"{sheet_name}!A1:Z"
    try:
        resp = _service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=range_name
        ).execute()
    except HttpError:
        return []
    return resp.get('values', [])

def update_row(sheet_name: str, row_index: int, values: list[str]):
    a1 = f"{sheet_name}!A{row_index+1}:Z{row_index+1}"
    _service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=a1,
        valueInputOption='RAW',
        body={'values': [values]}
    ).execute()

def append_row(sheet_name: str, values: list[str]):
    _service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A1:Z",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [values]}
    ).execute()

def clear_sheet(sheet_name: str):
    _service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A2:Z"
    ).execute()

def ensure_sheet(tab_name: str, header: list[str]):
    meta = _service.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        fields="sheets.properties.title"
    ).execute()
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]

    if tab_name not in titles:
        _service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
        ).execute()
        append_row(tab_name, header)

def update_player_premium_credits(player_id: str, change: int):
    players = get_rows('Players')
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == player_id:
            current = int(row[7]) if len(row) > 7 else 0
            new_value = current + change
            while len(row) < 8:
                row.append('0')
            row[7] = str(new_value)
            update_row('Players', idx, row)
            break
