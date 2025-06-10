import os
import base64
import json
import datetime
from typing import Optional, Dict, Any, List

import gspread
from google.oauth2.service_account import Credentials
from gspread import WorksheetNotFound

# Module-level variables to hold the authenticated sheet and "Players" worksheet
_gc: Optional[gspread.Client] = None
_sheet: Optional[gspread.Spreadsheet] = None
_players_ws: Optional[gspread.Worksheet] = None

# The exact headers (in this order) we require on the "Players" worksheet:
REQUIRED_HEADERS = [
    "user_id", "telegram_username", "game_name", "registered_at",
    "resources_wood", "resources_stone", "resources_gold", "resources_food",
    "diamonds", "base_level", "coord_x", "coord_y",
    "town_hall_level", "lumber_mill_level", "quarry_level", "mine_level", "farm_level"
]

def _load_credentials_info(base64_creds: str) -> Dict[str, Any]:
    """Decodes BASE64_CREDS, handling raw JSON or base64-encoded strings."""
    try:
        # Try decoding as base64 first
        creds_json_bytes = base64.b64decode(base64_creds)
        return json.loads(creds_json_bytes)
    except (base64.binascii.Error, json.JSONDecodeError):
        # If base64 decoding fails, try loading as raw JSON
        if base64_creds.strip().startswith("{"):
            try:
                return json.loads(base64_creds)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in BASE64_CREDS: {e}")
        else:
            raise ValueError("BASE64_CREDS is neither valid base64 nor raw JSON.")

def _authenticate_and_open_sheet() -> None:
    """Authenticates to Google Sheets and opens the target spreadsheet."""
    global _gc, _sheet

    b64_creds = os.getenv("BASE64_CREDS")
    sheet_id = os.getenv("SHEET_ID")

    if not b64_creds:
        raise RuntimeError("BASE64_CREDS environment variable is not set.")
    if not sheet_id:
        raise RuntimeError("SHEET_ID environment variable is not set.")

    try:
        info = _load_credentials_info(b64_creds)
    except ValueError as e:
        raise RuntimeError(f"Failed to load credentials: {e}") from e

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(info, scopes=scopes)
        _gc = gspread.authorize(credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to authorize gspread client: {e}") from e

    try:
        _sheet = _gc.open_by_key(sheet_id)
    except Exception as e:
        raise RuntimeError(f"Failed to open Google Sheet (ID='{sheet_id}'): {e}") from e

def _ensure_players_worksheet() -> None:
    """Ensures the 'Players' worksheet exists with correct headers."""
    global _players_ws

    try:
        _players_ws = _sheet.worksheet("Players")
    except WorksheetNotFound:
        # Create new worksheet if it doesn't exist
        _players_ws = _sheet.add_worksheet(
            title="Players", 
            rows=1000, 
            cols=len(REQUIRED_HEADERS)
        )
        _players_ws.append_row(REQUIRED_HEADERS)
        return

    # If worksheet exists, check and update headers
    existing_headers = _players_ws.row_values(1)
    
    # Ensure all REQUIRED_HEADERS are present and in the correct order
    headers_to_append = []
    for required_header in REQUIRED_HEADERS:
        if required_header not in existing_headers:
            headers_to_append.append(required_header)
    
    if headers_to_append:
        # Append missing headers to the end of the first row
        # Fetch current headers again to ensure we append correctly if sheet changed
        current_headers = _players_ws.row_values(1)
        new_headers_row = current_headers + headers_to_append
        _players_ws.update_cell(1, 1, new_headers_row[0]) # Update first cell to trigger row update
        for i, header in enumerate(new_headers_row):
            _players_ws.update_cell(1, i + 1, header)


def initialize_sheets() -> None:
    """Initializes the Google Sheets connection and ensures the Players worksheet exists."""
    if _gc and _sheet and _players_ws: # Already initialized
        return

    _authenticate_and_open_sheet()
    _ensure_players_worksheet()

def get_player_row(user_id: int) -> Optional[int]:
    """Returns the 1-based row index for a given user_id in the Players worksheet.
    Returns None if the user_id is not found.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")

    try:
        # Search in the first column (user_id)
        cell = _players_ws.find(str(user_id), in_column=1)
        return cell.row
    except gspread.exceptions.CellNotFound:
        return None
    except Exception as e:
        raise RuntimeError(f"Error finding player row for user_id {user_id}: {e}") from e

def create_new_player(user_id: int, telegram_username: str, game_name: str) -> None:
    """Appends a new row for a player with default starting values."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")

    if get_player_row(user_id) is not None:
        raise ValueError(f"Player with user_id {user_id} already exists.")

    now_utc_iso = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    new_row_values = [
        str(user_id),
        telegram_username or "",
        game_name,
        now_utc_iso,
        1000,  # resources_wood
        1000,  # resources_stone
        500,   # resources_gold
        500,   # resources_food
        0,     # diamonds
        1,     # base_level
        0,     # coord_x (default)
        0,     # coord_y (default)
        1,     # town_hall_level (default)
        1,     # lumber_mill_level (default)
        1,     # quarry_level (default)
        1,     # mine_level (default)
        1      # farm_level (default)
    ]

    try:
        _players_ws.append_row(new_row_values)
    except Exception as e:
        raise RuntimeError(f"Failed to create new player entry for user_id {user_id}: {e}") from e

def get_player_data(user_id: int) -> Dict[str, Any]:
    """Retrieves all data for a player as a dictionary, casting numeric values to int.
    Returns an empty dictionary if the player is not found.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")

    row_index = get_player_row(user_id)
    if row_index is None:
        return {}

    try:
        headers = _players_ws.row_values(1)
        values = _players_ws.row_values(row_index)
        
        player_data = {}
        for i, header in enumerate(headers):
            value = values[i] if i < len(values) else ""
            # Attempt to cast numeric values to int
            if header in [
                "user_id", "resources_wood", "resources_stone", "resources_gold",
                "resources_food", "diamonds", "base_level", "coord_x", "coord_y",
                "town_hall_level", "lumber_mill_level", "quarry_level", "mine_level", "farm_level"
            ]:
                try:
                    player_data[header] = int(value)
                except ValueError:
                    player_data[header] = 0 # Default to 0 if cannot convert
            else:
                player_data[header] = value
        return player_data
    except Exception as e:
        raise RuntimeError(f"Error retrieving player data for user_id {user_id}: {e}") from e

def update_player_data(user_id: int, field: str, new_value: Any) -> None:
    """Updates a specific field for a player.
    Raises ValueError if the user is not found or the field/column does not exist.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")

    row_index = get_player_row(user_id)
    if row_index is None:
        raise ValueError(f"Player with user_id {user_id} not found for update.")

    headers = _players_ws.row_values(1)
    try:
        col_index = headers.index(field) + 1 # gspread columns are 1-based
    except ValueError:
        raise ValueError(f"Field '{field}' does not exist as a column in the Players worksheet.")

    try:
        _players_ws.update_cell(row_index, col_index, str(new_value))
    except Exception as e:
        raise RuntimeError(f"Failed to update field '{field}' for user_id {user_id}: {e}") from e

def list_all_players() -> List[Dict[str, Any]]:
    """Lists all players as a list of dictionaries, casting numeric values to int.
    Each dictionary maps headers to values.
    """
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")

    try:
        all_values = _players_ws.get_all_values()
        if not all_values: # Empty sheet or only headers, no data rows
            return []
        
        headers = all_values[0]
        data_rows = all_values[1:]

        players_list = []
        for row_values in data_rows:
            player_data = {}
            for i, header in enumerate(headers):
                value = row_values[i] if i < len(row_values) else ""
                # Attempt to cast numeric values to int
                if header in [
                    "user_id", "resources_wood", "resources_stone", "resources_gold",
                    "resources_food", "diamonds", "base_level", "coord_x", "coord_y",
                    "town_hall_level", "lumber_mill_level", "quarry_level", "mine_level", "farm_level"
                ]:
                    try:
                        player_data[header] = int(value)
                    except ValueError:
                        player_data[header] = 0 # Default to 0 if cannot convert
                else:
                    player_data[header] = value
            players_list.append(player_data)
        return players_list
    except Exception as e:
        raise RuntimeError(f"Error listing all players: {e}") from e

# Cursor Prompt (for future regeneration):
# "Generate a file modules/sheets_helper.py that decodes BASE64_CREDS,
#  authenticates to Google Sheets via google-auth and gspread, ensures
#  a 'Players' worksheet with the specified headers exists, and exposes
#  helper functions: initialize_sheets(), get_player_row(), create_new_player(),
#  get_player_data(), update_player_data(), list_all_players(). Use ISO timestamps,
#  Python types for sheet values, and handle missing-column or missing-sheet cases gracefully." 