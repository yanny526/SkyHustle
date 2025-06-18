# src/utils/google_sheets.py
import os
import gspread
import json
import base64
import logging
from io import StringIO # Used for in-memory file-like object

# Import constants for sheet headers
from src.core import constants

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

_sheet_client = None # Cache the gspread client

def _get_sheet_client():
    """
    Authenticates with Google Sheets using base64-encoded credentials from environment.
    Caches the client for subsequent calls.
    """
    global _sheet_client
    if _sheet_client:
        return _sheet_client

    try:
        base64_creds = os.environ.get('BASE64_CREDS')
        if not base64_creds:
            raise ValueError("BASE64_CREDS environment variable not set. Cannot authenticate Google Sheets.")

        creds_json_str = base64.b64decode(base64_creds).decode('utf-8')
        creds_dict = json.loads(creds_json_str)

        _sheet_client = gspread.service_account_from_dict(creds_dict)
        logger.info("Successfully authenticated with Google Sheets.")
        return _sheet_client
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to authenticate with Google Sheets. Check BASE64_CREDS: {e}")
        raise # Re-raise to halt execution if authentication fails

def _initialize_player_worksheet(spreadsheet):
    """
    Ensures the 'Players' worksheet exists and has the correct headers.
    """
    try:
        # Try to get the 'Players' worksheet
        try:
            worksheet = spreadsheet.worksheet('Players')
            logger.info("Existing 'Players' worksheet found.")
        except gspread.exceptions.WorksheetNotFound:
            # If not found, create it
            worksheet = spreadsheet.add_worksheet(title='Players', rows=1, cols=len(constants.SHEET_COLUMN_HEADERS))
            logger.info("Created new 'Players' worksheet.")
        
        # Check if headers are set correctly
        current_headers = worksheet.row_values(1)
        if current_headers != constants.SHEET_COLUMN_HEADERS:
            worksheet.update([constants.SHEET_COLUMN_HEADERS], range_name='A1')
            logger.info("Updated 'Players' worksheet headers.")
        else:
            logger.info("'Players' worksheet headers are already correct.")
            
        return worksheet
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to initialize 'Players' worksheet: {e}")
        raise

def get_worksheet():
    """
    Retrieves the main game worksheet ('Players') and ensures its proper setup.
    """
    try:
        client = _get_sheet_client()
        sheet_id = os.environ.get('SHEET_ID')
        if not sheet_id:
            raise ValueError("SHEET_ID environment variable not set. Cannot open Google Sheet.")
        
        try:
            spreadsheet = client.open_by_key(sheet_id)
            logger.info(f"Connected to Google Spreadsheet: {spreadsheet.title}")
        except gspread.exceptions.SpreadsheetNotFound:
            logger.critical(f"CRITICAL ERROR: Google Spreadsheet with ID '{sheet_id}' not found. "
                             "Please ensure the SHEET_ID is correct and the Service Account has 'Editor' access.")
            raise # Halt if the main spreadsheet doesn't exist or isn't accessible

        worksheet = _initialize_player_worksheet(spreadsheet)
        return worksheet
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to get or initialize worksheet: {e}")
        raise

def find_player_row(user_id):
    """
    Finds a player's row in the worksheet by user_id.
    Returns the row index (1-based) and the record (dict).
    """
    try:
        worksheet = get_worksheet()
        # Find cell containing user_id in the first column
        cell = worksheet.find(str(user_id), in_column=1) 
        if cell:
            row_index = cell.row
            player_data = worksheet.row_values(row_index)
            headers = worksheet.row_values(1) # Re-fetch headers to ensure accuracy
            return row_index, dict(zip(headers, player_data))
        return None, None
    except Exception as e:
        logger.error(f"Error finding player {user_id}: {e}")
        return None, None

def create_player_row(player_data_dict):
    """Appends a new player's data as a row in the worksheet."""
    try:
        worksheet = get_worksheet()
        headers = worksheet.row_values(1)
        row_to_append = [player_data_dict.get(header, '') for header in headers]
        
        worksheet.append_row(row_to_append)
        logger.info(f"New player {player_data_dict.get('user_id')} created in sheet.")
        return True
    except Exception as e:
        logger.error(f"Error creating new player row for {player_data_dict.get('user_id')}: {e}")
        return False

def update_player_row(row_index, data_to_update_dict):
    """Updates specific cells in an existing player's row."""
    try:
        worksheet = get_worksheet()
        headers = worksheet.row_values(1)
        
        updates = []
        for key, value in data_to_update_dict.items():
            if key in headers:
                col_index = headers.index(key) + 1 # +1 because gspread is 1-based index
                updates.append({
                    'range': gspread.utils.rowcol_to_a1(row_index, col_index),
                    'values': [[value]]
                })
        
        if updates:
            worksheet.batch_update(updates)
            logger.info(f"Player data at row {row_index} updated.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating player row {row_index}: {e}")
        return False