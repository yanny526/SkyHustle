# google_sheets.py
# System 9 Upgrade: Now a powerful, multi-sheet engine capable of managing both Players and Alliances.

import os
import gspread
import json
import base64
import logging
from datetime import datetime, timezone
import constants

logger = logging.getLogger(__name__)
_sheet_client = None
_spreadsheet = None

def _get_spreadsheet():
    """Establishes connection to the Google Sheet and caches it."""
    global _sheet_client, _spreadsheet
    if _spreadsheet:
        return _spreadsheet

    if not _sheet_client:
        try:
            base64_creds = os.environ.get('BASE64_CREDS')
            creds_json_str = base64.b64decode(base64_creds).decode('utf-8')
            creds_dict = json.loads(creds_json_str)
            _sheet_client = gspread.service_account_from_dict(creds_dict)
            logger.info("Successfully authenticated with Google Sheets.")
        except Exception as e:
            logger.critical(f"CRITICAL ERROR: Failed to authenticate with Google Sheets: {e}")
            raise

    try:
        sheet_id = os.environ.get('SHEET_ID')
        _spreadsheet = _sheet_client.open_by_key(sheet_id)
        logger.info(f"Connected to Google Spreadsheet: {_spreadsheet.title}")
        return _spreadsheet
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to open spreadsheet with ID. Check SHEET_ID. Error: {e}")
        raise

def _get_or_create_worksheet(name: str, headers: list):
    """Internal helper to get a worksheet by name or create it with headers if it doesn't exist."""
    spreadsheet = _get_spreadsheet()
    try:
        worksheet = spreadsheet.worksheet(name)
        logger.info(f"Found existing '{name}' worksheet.")
    except gspread.exceptions.WorksheetNotFound:
        logger.warning(f"'{name}' worksheet not found. Creating it...")
        worksheet = spreadsheet.add_worksheet(title=name, rows=1, cols=len(headers))
        logger.info(f"Successfully created '{name}' worksheet.")

    # Verify and set headers if they are incorrect.
    current_headers = worksheet.row_values(1)
    if current_headers != headers:
        logger.info(f"'{name}' worksheet headers are missing or incorrect. Setting headers...")
        worksheet.update([headers], range_name='A1')
        logger.info(f"Successfully set '{name}' worksheet headers.")
    return worksheet

# --- PUBLIC FUNCTIONS ---

def get_players_worksheet():
    """Public-facing function to get the Players worksheet."""
    return _get_or_create_worksheet('Players', constants.SHEET_COLUMN_HEADERS)

def get_alliances_worksheet():
    """Public-facing function to get the Alliances worksheet."""
    return _get_or_create_worksheet('Alliances', constants.ALLIANCES_SHEET_COLUMN_HEADERS)

def find_player_row(user_id: int):
    try:
        worksheet = get_players_worksheet()
        cell = worksheet.find(str(user_id), in_column=1)
        if cell:
            headers = worksheet.row_values(1)
            player_data = worksheet.row_values(cell.row)
            return cell.row, dict(zip(headers, player_data))
        return None, None
    except Exception as e:
        logger.error(f"Error finding player {user_id}: {e}")
        return None, None

def find_player_by_name(commander_name: str):
    try:
        worksheet = get_players_worksheet()
        headers = worksheet.row_values(1)
        name_col_index = headers.index(constants.FIELD_COMMANDER_NAME) + 1
        cell = worksheet.find(commander_name, in_column=name_col_index)
        if cell:
            player_data = worksheet.row_values(cell.row)
            return cell.row, dict(zip(headers, player_data))
        return None, None
    except Exception as e:
        logger.error(f"Error finding player by name '{commander_name}': {e}")
        return None, None

def update_player_data(user_id: int, updates: dict):
    try:
        worksheet = get_players_worksheet()
        row_index, _ = find_player_row(user_id)
        if not row_index: return False
        headers = worksheet.row_values(1)
        cell_updates = []
        for key, value in updates.items():
            if key in headers:
                col_index = headers.index(key) + 1
                cell_updates.append(gspread.Cell(row_index, col_index, str(value)))
        if cell_updates: worksheet.update_cells(cell_updates, value_input_option='USER_ENTERED')
        logger.info(f"Successfully updated player data for user {user_id}: {updates}")
        return True
    except Exception as e:
        logger.error(f"Error updating data for player {user_id}: {e}")
        return False

def create_player_row(player_data_dict: dict):
    try:
        worksheet = get_players_worksheet()
        now_utc, shield_finish_time = datetime.now(timezone.utc), (datetime.now(timezone.utc) + constants.INITIAL_PLAYER_STATS['shield_finish_time'])
        player_data_dict['shield_finish_time'] = shield_finish_time.isoformat()
        player_data_dict['created_at'] = now_utc.isoformat()
        player_data_dict['last_seen'] = now_utc.isoformat()
        row_to_append = [player_data_dict.get(header, '') for header in constants.SHEET_COLUMN_HEADERS]
        worksheet.append_row(row_to_append)
        logger.info(f"Successfully created new player row for user_id {player_data_dict.get('user_id')}.")
        return True
    except Exception as e:
        logger.error(f"Error creating new player row for {player_data_dict.get('user_id')}: {e}")
        return False

# --- NEW: Alliance Management Functions ---

def create_alliance(alliance_data: dict):
    """Appends a new alliance's data to the Alliances worksheet."""
    try:
        worksheet = get_alliances_worksheet()
        alliance_data['created_at'] = datetime.now(timezone.utc).isoformat()
        
        row_to_append = [alliance_data.get(header, '') for header in constants.ALLIANCES_SHEET_COLUMN_HEADERS]
        worksheet.append_row(row_to_append)
        logger.info(f"Successfully created new alliance: {alliance_data.get('alliance_name')}")
        return True
    except Exception as e:
        logger.error(f"Error creating new alliance: {e}")
        return False