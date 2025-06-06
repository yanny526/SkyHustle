import os
import base64
import json
import datetime
from typing import Optional, Dict, Any, List

import gspread
from google.oauth2.service_account import Credentials

# ------------------------------------------------------------------------------
# Module-level variables to hold the authenticated sheet and "Players" worksheet
# ------------------------------------------------------------------------------
_gc = None            # type: gspread.Client
_sheet = None         # type: gspread.Spreadsheet
_players_ws = None    # type: gspread.Worksheet

# The exact headers (in this order) we require on the "Players" worksheet:
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
]

# Required OAuth scopes for reading/writing Google Sheets & Drive
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ------------------------------------------------------------------------------
# Internal: decode (if needed) BASE64_CREDS, authenticate to Google Sheets, and open the sheet
# ------------------------------------------------------------------------------
def _authenticate_and_open_sheet() -> None:
    """
    Decode BASE64_CREDS if necessary, authenticate via google.oauth2.service_account to gspread.
    Then open the Google Sheet whose ID is in SHEET_ID and assign to module variables.
    Raises an Exception if any step fails.
    """
    global _gc, _sheet

    # 1) Read environment variables
    raw_creds = os.getenv("BASE64_CREDS")
    sheet_id = os.getenv("SHEET_ID")

    if not raw_creds:
        raise RuntimeError("BASE64_CREDS not found in environment variables.")
    if not sheet_id:
        raise RuntimeError("SHEET_ID not found in environment variables.")

    # 2) Determine if raw_creds is already JSON or needs base64 decoding
    try:
        raw_creds_stripped = raw_creds.strip()
        if raw_creds_stripped.startswith("{"):
            # Looks like plain JSON—parse directly
            info = json.loads(raw_creds_stripped)
        else:
            # Assume base64-encoded JSON
            decoded = base64.b64decode(raw_creds_stripped)
            info = json.loads(decoded)
    except Exception as e:
        raise RuntimeError(f"Failed to parse BASE64_CREDS as JSON or base64: {e}")

    # 3) Create Credentials object for gspread with proper scopes
    try:
        credentials = Credentials.from_service_account_info(info, scopes=_SCOPES)
        _gc = gspread.authorize(credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to authorize gspread client with scopes {_SCOPES}: {e}")

    # 4) Open the spreadsheet by ID
    try:
        _sheet = _gc.open_by_key(sheet_id)
    except Exception as e:
        raise RuntimeError(f"Failed to open Google Sheet (ID={sheet_id}): {e}")


# ------------------------------------------------------------------------------
# Internal: ensure the "Players" worksheet exists with correct headers
# ------------------------------------------------------------------------------
def _ensure_players_worksheet() -> None:
    """
    Ensure that there is a worksheet titled "Players" in the spreadsheet.
    If not, create it and write the exact headers from _PLAYERS_HEADERS.
    If it already exists, verify that each header in _PLAYERS_HEADERS is present
    in the correct order (appending any missing columns at the end).
    """
    global _players_ws

    # Attempt to fetch an existing worksheet named "Players"
    try:
        _players_ws = _sheet.worksheet("Players")
    except gspread.exceptions.WorksheetNotFound:
        # Create a new "Players" worksheet with default rows/cols
        _players_ws = _sheet.add_worksheet(
            title="Players", rows="100", cols=str(len(_PLAYERS_HEADERS))
        )
        _players_ws.append_row(_PLAYERS_HEADERS)
        return

    # If worksheet exists, check headers
    existing = _players_ws.row_values(1)
    to_append = []
    for idx, header in enumerate(_PLAYERS_HEADERS):
        if idx < len(existing) and existing[idx] == header:
            continue
        elif header not in existing:
            to_append.append(header)

    if to_append:
        updated_headers = existing + to_append
        _players_ws.delete_rows(1)
        _players_ws.insert_row(updated_headers, index=1)
    # Any extra columns beyond our list remain intact.


# ------------------------------------------------------------------------------
# Public: initialize_sheets()
# ------------------------------------------------------------------------------
def initialize_sheets() -> None:
    """
    Call this once at bot startup. It will:
      1. Decode (if needed) BASE64_CREDS and authenticate to Google Sheets using proper scopes.
      2. Open the spreadsheet by SHEET_ID.
      3. Ensure a worksheet named "Players" exists with the correct headers.
    After this, other helper functions (get_player_row, create_new_player, etc.)
    can be used safely.
    """
    if _gc and _sheet and _players_ws:
        return  # already done

    _authenticate_and_open_sheet()
    _ensure_players_worksheet()


# ------------------------------------------------------------------------------
# Public: get_player_row(user_id)
# ------------------------------------------------------------------------------
def get_player_row(user_id: int) -> Optional[int]:
    """
    Return the 1-based row index in "Players" where the user_id matches.
    If no match, return None.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets have not been initialized. Call initialize_sheets() first.")

    try:
        all_values = _players_ws.get_all_values()
        for row_idx in range(2, len(all_values) + 1):
            cell_value = all_values[row_idx - 1][0]
            if cell_value and int(cell_value) == user_id:
                return row_idx
        return None
    except Exception as e:
        raise RuntimeError(f"Error reading from 'Players' sheet: {e}")


# ------------------------------------------------------------------------------
# Public: create_new_player(user_id, telegram_username, game_name)
# ------------------------------------------------------------------------------
def create_new_player(user_id: int, telegram_username: str, game_name: str) -> None:
    """
    Append a new row to the "Players" worksheet with these values:
      user_id, telegram_username, game_name, registered_at (ISO UTC),
      resources_wood=1000, resources_stone=1000, resources_gold=500,
      resources_food=500, diamonds=0, base_level=1.

    Raises an error if the user already exists.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets have not been initialized. Call initialize_sheets() first.")

    existing_row = get_player_row(user_id)
    if existing_row is not None:
        raise ValueError(f"User ID {user_id} already exists in Players sheet at row {existing_row}.")

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
    ]

    try:
        _players_ws.append_row(new_row)
    except Exception as e:
        raise RuntimeError(f"Failed to append new player row: {e}")


# ------------------------------------------------------------------------------
# Public: get_player_data(user_id)
# ------------------------------------------------------------------------------
def get_player_data(user_id: int) -> Dict[str, Any]:
    """
    Return a dict mapping each column header to its value (cast to int or str) for the given user_id.
    If user_id not found, return an empty dict.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets have not been initialized. Call initialize_sheets() first.")

    row_idx = get_player_row(user_id)
    if row_idx is None:
        return {}

    try:
        headers = _players_ws.row_values(1)
        values = _players_ws.row_values(row_idx)
        result: Dict[str, Any] = {}
        for idx, header in enumerate(headers):
            if idx >= len(values):
                result[header] = ""
                continue
            cell = values[idx]
            if header in [
                "user_id",
                "resources_wood",
                "resources_stone",
                "resources_gold",
                "resources_food",
                "diamonds",
                "base_level",
            ]:
                try:
                    result[header] = int(cell)
                except:
                    result[header] = 0
            else:
                result[header] = cell
        return result
    except Exception as e:
        raise RuntimeError(f"Error retrieving player data for user_id {user_id}: {e}")


# ------------------------------------------------------------------------------
# Public: update_player_data(user_id, field, new_value)
# ------------------------------------------------------------------------------
def update_player_data(user_id: int, field: str, new_value: Any) -> None:
    """
    Find the player's row, then locate the column named `field` and update its value to `new_value`.
    If the user or field does not exist, raise a clear error.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets have not been initialized. Call initialize_sheets() first.")

    row_idx = get_player_row(user_id)
    if row_idx is None:
        raise ValueError(f"User ID {user_id} not found in Players sheet.")

    try:
        headers = _players_ws.row_values(1)
        if field not in headers:
            raise ValueError(f"Field '{field}' does not exist in Players worksheet.")
        col_idx = headers.index(field) + 1
        _players_ws.update_cell(row_idx, col_idx, new_value)
    except Exception as e:
        raise RuntimeError(f"Failed to update field '{field}' for user_id {user_id}: {e}")


# ------------------------------------------------------------------------------
# Public: list_all_players()
# ------------------------------------------------------------------------------
def list_all_players() -> List[Dict[str, Any]]:
    """
    Return a list of all players in the "Players" worksheet, where each player is represented
    as a dict mapping column names to values (cast to int or str). Useful for leaderboards.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets have not been initialized. Call initialize_sheets() first.")

    try:
        all_values = _players_ws.get_all_values()
        headers = all_values[0]
        rows = all_values[1:]

        players_list: List[Dict[str, Any]] = []
        for row in rows:
            entry: Dict[str, Any] = {}
            for idx, header in enumerate(headers):
                if idx >= len(row):
                    entry[header] = ""
                    continue
                cell = row[idx]
                if header in [
                    "user_id",
                    "resources_wood",
                    "resources_stone",
                    "resources_gold",
                    "resources_food",
                    "diamonds",
                    "base_level",
                ]:
                    try:
                        entry[header] = int(cell)
                    except:
                        entry[header] = 0
                else:
                    entry[header] = cell
            players_list.append(entry)
        return players_list
    except Exception as e:
        raise RuntimeError(f"Error listing all players: {e}")


# ------------------------------------------------------------------------------
# Cursor Prompt (for future regeneration):
# “Generate a file modules/sheets_helper.py that:
#  1. Reads BASE64_CREDS from env, detecting if it’s raw JSON or base64-encoded JSON.
#  2. Authenticates to Google Sheets with scopes 
#     https://www.googleapis.com/auth/spreadsheets and 
#     https://www.googleapis.com/auth/drive.
#  3. Ensures a 'Players' worksheet with headers 
#     [user_id, telegram_username, game_name, registered_at, resources_wood, resources_stone, resources_gold, resources_food, diamonds, base_level].
#  4. Exposes helper functions: initialize_sheets(), get_player_row(), create_new_player(), get_player_data(), update_player_data(), list_all_players().”
# ------------------------------------------------------------------------------
