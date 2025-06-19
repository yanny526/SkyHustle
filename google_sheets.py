# google_sheets.py
# Upgraded to include a generic, efficient multi-cell update function.

import os
import gspread
import json
import base64
import logging
from datetime import datetime, timezone
import constants

logger = logging.getLogger(__name__)
_sheet_client = None

# _get_sheet_client() function remains the same...
def _get_sheet_client():
    global _sheet_client
    if _sheet_client: return _sheet_client
    try:
        base64_creds = os.environ.get('BASE64_CREDS')
        creds_json_str = base64.b64decode(base64_creds).decode('utf-8')
        creds_dict = json.loads(creds_json_str)
        _sheet_client = gspread.service_account_from_dict(creds_dict)
        logger.info("Successfully authenticated with Google Sheets.")
        return _sheet_client
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to authenticate with Google Sheets: {e}")
        raise

# get_worksheet() function remains the same...
def get_worksheet(worksheet_name='Players'):
    try:
        client = _get_sheet_client()
        sheet_id = os.environ.get('SHEET_ID')
        spreadsheet = client.open_by_key(sheet_id)
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            logger.warning(f"'{worksheet_name}' worksheet not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=len(constants.SHEET_COLUMN_HEADERS))
        current_headers = worksheet.row_values(1)
        if current_headers != constants.SHEET_COLUMN_HEADERS:
            logger.info("Worksheet headers are missing or incorrect. Setting headers...")
            worksheet.update(values=[constants.SHEET_COLUMN_HEADERS], range_name='A1')
            logger.info("Successfully set worksheet headers.")
        return worksheet
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to get or initialize worksheet: {e}")
        raise

# find_player_row() function remains the same...
def find_player_row(user_id: int):
    try:
        worksheet = get_worksheet()
        cell = worksheet.find(str(user_id), in_column=1)
        if cell:
            headers = worksheet.row_values(1)
            player_data = worksheet.row_values(cell.row)
            return cell.row, dict(zip(headers, player_data))
        return None, None
    except Exception as e:
        logger.error(f"Error finding player {user_id}: {e}")
        return None, None

# --- NEW: A generic, powerful function to update multiple player attributes at once ---
def update_player_data(user_id: int, updates: dict):
    """
    Finds a player by user_id and updates their data with the key-value pairs in the updates dictionary.
    Returns True on success, False on failure.
    """
    try:
        worksheet = get_worksheet()
        row_index, player_data = find_player_row(user_id)
        if not row_index:
            logger.error(f"Cannot update data for non-existent player {user_id}.")
            return False
        
        headers = worksheet.row_values(1)
        # Prepare a list of cell objects to update in a single batch request for max efficiency.
        cell_updates = []
        for key, value in updates.items():
            if key in headers:
                col_index = headers.index(key) + 1 # gspread is 1-indexed
                cell_updates.append(gspread.Cell(row_index, col_index, str(value)))
            else:
                logger.warning(f"Attempted to update non-existent column '{key}' for user {user_id}.")
        
        if cell_updates:
            worksheet.update_cells(cell_updates, value_input_option='USER_ENTERED')
            logger.info(f"Successfully updated data for user {user_id}: {updates}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating data for player {user_id}: {e}")
        return False

# create_player_row() function remains the same...
def create_player_row(player_data_dict: dict):
    try:
        worksheet = get_worksheet()
        now_utc = datetime.now(timezone.utc).isoformat()
        player_data_dict['created_at'] = now_utc
        player_data_dict['last_seen'] = now_utc
        row_to_append = [player_data_dict.get(header, '') for header in constants.SHEET_COLUMN_HEADERS]
        worksheet.append_row(row_to_append)
        logger.info(f"Successfully created new player row for user_id {player_data_dict.get('user_id')}.")
        return True
    except Exception as e:
        logger.error(f"Error creating new player row for {player_data_dict.get('user_id')}: {e}")
        return False