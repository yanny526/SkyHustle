import os
import base64
import json
import datetime
import random
from typing import Optional, Dict, Any, List

import gspread
from google.oauth2.service_account import Credentials
from gspread import WorksheetNotFound

# ------------------------------------------------------------------------------
# Module-level variables
# ------------------------------------------------------------------------------
_gc = None            # type: gspread.Client
_sheet = None         # type: gspread.Spreadsheet
_players_ws = None    # type: gspread.Worksheet

# The exact headers we require on the "Players" worksheet:
_PLAYERS_HEADERS = [
    "user_id",
    "telegram_username",
    "game_name",
    "registered_at",
    "resources_wood",
    "resources_stone",
    "resources_gold",
    "resources_food",
    "diamonds",
    "base_level",
    "coord_x",
    "coord_y",
    "lumber_house_level",
    "mine_level",
    "warehouse_level",
    "hospital_level",
    "research_lab_level",
    "barracks_level",
    "power_plant_level",
    "workshop_level",
    "jail_level",
    "army_infantry",
    "army_tank",
    "army_artillery",
    "army_destroyer",
]

# Required OAuth scopes for reading/writing Google Sheets & Drive
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _authenticate_and_open_sheet() -> None:
    """Authenticate to Google Sheets using BASE64_CREDS and open the spreadsheet."""
    global _gc, _sheet

    raw_creds = os.getenv("BASE64_CREDS")
    sheet_id = os.getenv("SHEET_ID")
    if not raw_creds or not sheet_id:
        raise RuntimeError("BASE64_CREDS and SHEET_ID must be set in environment variables.")

    try:
        creds_json = json.loads(raw_creds) if raw_creds.strip().startswith("{") else json.loads(base64.b64decode(raw_creds))
    except Exception as e:
        raise RuntimeError(f"Failed to parse BASE64_CREDS as JSON or base64: {e}")

    credentials = Credentials.from_service_account_info(creds_json, scopes=_SCOPES)
    _gc = gspread.authorize(credentials)
    _sheet = _gc.open_by_key(sheet_id)

def _ensure_players_worksheet() -> None:
    """Ensure that the "Players" worksheet exists with the correct headers."""
    global _players_ws

    try:
        _players_ws = _sheet.worksheet("Players")
    except gspread.exceptions.WorksheetNotFound:
        _players_ws = _sheet.add_worksheet(title="Players", rows="100", cols=str(len(_PLAYERS_HEADERS)))
        _players_ws.append_row(_PLAYERS_HEADERS)
        return

    existing = _players_ws.row_values(1)
    to_append = [h for h in _PLAYERS_HEADERS if h not in existing]
    if to_append:
        updated_headers = existing + to_append
        _players_ws.update('A1', [updated_headers])

def initialize_sheets() -> None:
    """Initialize Google Sheets client and ensure the Players worksheet exists."""
    if _gc and _sheet and _players_ws:
        return
    _authenticate_and_open_sheet()
    _ensure_players_worksheet()

def get_player_row(user_id: int) -> Optional[int]:
    """Return the row number where user_id matches, or None if not found."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    all_vals = _players_ws.get_all_values()
    for idx, row in enumerate(all_vals[1:], start=2):
        if str(row[0]) == str(user_id):
            return idx
    return None

def create_new_player(user_id: int, telegram_username: str, game_name: str) -> None:
    """Append a new player row with default resources, levels, and coordinates."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    if get_player_row(user_id) is not None:
        raise ValueError(f"User ID {user_id} already exists.")

    coord_x = random.randint(1, 1000)
    coord_y = random.randint(1, 1000)
    iso_now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    new_row = [
        user_id,
        telegram_username or "",
        game_name,
        iso_now,
        1000,  # resources_wood
        1000,  # resources_stone
        500,   # resources_gold
        500,   # resources_food
        0,     # diamonds
        1,     # base_level
        coord_x,
        coord_y,
        1,  # lumber_house_level
        1,  # mine_level
        1,  # warehouse_level
        1,  # hospital_level
        1,  # research_lab_level
        1,  # barracks_level
        1,  # power_plant_level
        1,  # workshop_level
        1,  # jail_level
        0,  # army_infantry
        0,  # army_tank
        0,  # army_artillery
        0,  # army_destroyer
    ]
    _players_ws.append_row(new_row)

def get_player_data(user_id: int) -> Dict[str, Any]:
    """Return a dict of all player fields, typed (int or str). Empty if not found."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    row_idx = get_player_row(user_id)
    if row_idx is None:
        return {}
    headers = _players_ws.row_values(1)
    values = _players_ws.row_values(row_idx)
    data: Dict[str, Any] = {}
    for i, h in enumerate(headers):
        val = values[i] if i < len(values) else ""
        if h in [
            "user_id", "resources_wood", "resources_stone", "resources_gold",
            "resources_food", "diamonds", "base_level", "coord_x", "coord_y",
            "lumber_house_level", "mine_level", "warehouse_level", "hospital_level",
            "research_lab_level", "barracks_level", "power_plant_level",
            "workshop_level", "jail_level",
            "army_infantry", "army_tank", "army_artillery", "army_destroyer"
        ]:
            try:
                data[h] = int(val)
            except:
                data[h] = 0
        else:
            data[h] = val
    return data

def update_player_data(user_id: int, field: str, new_value: Any) -> None:
    """Update a specific field for a player."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    row_idx = get_player_row(user_id)
    if row_idx is None:
        raise ValueError(f"User ID {user_id} not found.")
    headers = _players_ws.row_values(1)
    if field not in headers:
        raise ValueError(f"Field '{field}' does not exist.")
    col_idx = headers.index(field) + 1
    _players_ws.update_cell(row_idx, col_idx, new_value)

def list_all_players() -> List[Dict[str, Any]]:
    """Return a list of all players as dicts of header→value."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    all_vals = _players_ws.get_all_values()
    headers = all_vals[0]
    players: List[Dict[str, Any]] = []
    for row in all_vals[1:]:
        entry = {}
        for i, h in enumerate(headers):
            entry[h] = row[i] if i < len(row) else ""
        players.append(entry)
    return players

# Cursor Prompt (for future regeneration):
# "Generate a file modules/sheets_helper.py that decodes BASE64_CREDS,
#  authenticates to Google Sheets via google-auth and gspread, ensures
#  a 'Players' worksheet with the specified headers exists, and exposes
#  helper functions: initialize_sheets(), get_player_row(), create_new_player(),
#  get_player_data(), update_player_data(), list_all_players(). Use ISO timestamps,
#  Python types for sheet values, and handle missing-column or missing-sheet cases gracefully." 