 # google_sheets.py
# The robust, fault-tolerant interface to our Google Sheets database.
# Engineered for efficiency with connection caching and automatic sheet initialization.

import os
import gspread
import json
import base64
import logging
from datetime import datetime, timezone

# Import our single source of truth for constants
import constants

# Initialize a logger for this module
logger = logging.getLogger(__name__)

# A private, cached gspread client instance.
# This prevents re-authenticating for every single database call, a critical efficiency gain.
_sheet_client = None

def _get_sheet_client():
    """
    Authenticates with Google Sheets using base64-encoded credentials.
    Caches the client for subsequent calls to maximize performance.
    """
    global _sheet_client
    if _sheet_client:
        return _sheet_client

    try:
        base64_creds = os.environ.get('BASE64_CREDS')
        if not base64_creds:
            logger.critical("CRITICAL: BASE64_CREDS environment variable not set.")
            raise ValueError("BASE64_CREDS environment variable is not set.")

        creds_json_str = base64.b64decode(base64_creds).decode('utf-8')
        creds_dict = json.loads(creds_json_str)

        logger.info("Authenticating with Google Sheets...")
        _sheet_client = gspread.service_account_from_dict(creds_dict)
        logger.info("Successfully authenticated with Google Sheets.")
        return _sheet_client
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to authenticate with Google Sheets. Check BASE64_CREDS. Error: {e}")
        raise # Re-raise to halt execution if authentication fails

def get_worksheet(worksheet_name='Players'):
    """
    Retrieves the main game worksheet and ensures its proper setup.
    This function is idempotent: it creates and formats the sheet if it doesn't exist,
    ensuring a zero-manual-setup deployment.
    """
    try:
        client = _get_sheet_client()
        sheet_id = os.environ.get('SHEET_ID')
        if not sheet_id:
            raise ValueError("SHEET_ID environment variable is not set.")
        
        spreadsheet = client.open_by_key(sheet_id)
        logger.info(f"Connected to Google Spreadsheet: {spreadsheet.title}")

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"Found existing '{worksheet_name}' worksheet.")
        except gspread.exceptions.WorksheetNotFound:
            logger.warning(f"'{worksheet_name}' worksheet not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=len(constants.SHEET_COLUMN_HEADERS))
            logger.info(f"Successfully created '{worksheet_name}' worksheet.")

        # Verify and set headers if they are incorrect.
        current_headers = worksheet.row_values(1)
        if current_headers != constants.SHEET_COLUMN_HEADERS:
            logger.info("Worksheet headers are missing or incorrect. Setting headers...")
            worksheet.update([constants.SHEET_COLUMN_HEADERS], range_name='A1')
            logger.info("Successfully set worksheet headers.")
            
        return worksheet
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: Failed to get or initialize worksheet. Error: {e}")
        raise

def find_player_row(user_id: int):
    """
    Finds a player's row in the worksheet by their unique user_id.
    Returns the row index and the record as a dictionary.
    """
    try:
        worksheet = get_worksheet()
        cell = worksheet.find(str(user_id), in_column=1) # user_id is always in the first column
        if cell:
            logger.info(f"Found player with user_id {user_id} at row {cell.row}.")
            headers = worksheet.row_values(1)
            player_data = worksheet.row_values(cell.row)
            return cell.row, dict(zip(headers, player_data))
        logger.info(f"No player found with user_id {user_id}.")
        return None, None
    except Exception as e:
        logger.error(f"Error finding player {user_id}: {e}")
        return None, None

def create_player_row(player_data_dict: dict):
    """Appends a new player's data as a row in the worksheet."""
    try:
        worksheet = get_worksheet()
        # Ensure UTC timestamp for universal consistency
        now_utc = datetime.now(timezone.utc).isoformat()
        player_data_dict['created_at'] = now_utc
        player_data_dict['last_seen'] = now_utc
        
        # Build the row in the exact order of the sheet's headers.
        # This prevents data misalignment.
        row_to_append = [player_data_dict.get(header, '') for header in constants.SHEET_COLUMN_HEADERS]
        
        worksheet.append_row(row_to_append)
        user_id = player_data_dict.get('user_id', 'N/A')
        logger.info(f"Successfully created new player row for user_id {user_id}.")
        return True
    except Exception as e:
        user_id = player_data_dict.get('user_id', 'N/A')
        logger.error(f"Error creating new player row for user_id {user_id}: {e}")
        return False