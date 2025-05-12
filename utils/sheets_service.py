"""
Google Sheets service for SkyHustle.
Handles interaction with Google Sheets API for data persistence.
"""
import os
import json
import base64
import logging
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import BASE64_CREDS, SHEET_ID, SHEET_NAMES

logger = logging.getLogger(__name__)

# Cache for spreadsheet data
_sheet_cache = {}
_cache_expiry = {}
CACHE_TTL = 60  # seconds

def _get_credentials():
    """
    Get Google API credentials from environment variables.
    
    Returns:
        ServiceAccountCredentials or None if not available
    """
    try:
        # Try to get credentials from environment variable
        if BASE64_CREDS:
            creds_json = json.loads(base64.b64decode(BASE64_CREDS).decode('utf-8'))
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        else:
            logger.error("BASE64_CREDS environment variable not found")
            return None
    except Exception as e:
        logger.error(f"Error getting credentials: {e}")
        return None

def _get_sheet_client():
    """
    Get authenticated gspread client.
    
    Returns:
        gspread.Client or None if authentication failed
    """
    try:
        credentials = _get_credentials()
        if credentials:
            return gspread.authorize(credentials)
        return None
    except Exception as e:
        logger.error(f"Error authorizing sheets client: {e}")
        return None

def get_sheet_data(sheet_name, force_refresh=False):
    """
    Get data from a specific sheet.
    
    Args:
        sheet_name: Name of the sheet to read
        force_refresh: Force refresh from Google Sheets
        
    Returns:
        list: List of dictionaries representing rows in the sheet
    """
    global _sheet_cache, _cache_expiry
    
    # Check if we have cached data that hasn't expired
    cache_key = f"{SHEET_ID}_{sheet_name}"
    now = time.time()
    
    if not force_refresh and cache_key in _sheet_cache and now < _cache_expiry.get(cache_key, 0):
        return _sheet_cache[cache_key]
    
    try:
        client = _get_sheet_client()
        if not client:
            logger.error("Failed to get sheets client")
            return []
        
        # Open the spreadsheet and the specific worksheet
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all records
        records = worksheet.get_all_records()
        
        # Cache the data
        _sheet_cache[cache_key] = records
        _cache_expiry[cache_key] = now + CACHE_TTL
        
        return records
    except Exception as e:
        logger.error(f"Error getting sheet data for {sheet_name}: {e}")
        
        # Return cached data if available, even if expired
        if cache_key in _sheet_cache:
            logger.warning(f"Returning stale cached data for {sheet_name}")
            return _sheet_cache[cache_key]
        
        return []

def update_sheet_data(sheet_name, record, key_field, key_value):
    """
    Update a record in a sheet based on a key field.
    
    Args:
        sheet_name: Name of the sheet to update
        record: Dictionary of data to update
        key_field: Field name to match for finding the row
        key_value: Value to match in key_field
        
    Returns:
        bool: Success or failure
    """
    try:
        client = _get_sheet_client()
        if not client:
            logger.error("Failed to get sheets client")
            return False
        
        # Open the spreadsheet and the specific worksheet
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all records to find the matching row
        records = worksheet.get_all_records()
        headers = worksheet.row_values(1)
        
        # Find the record to update
        row_index = None
        for i, r in enumerate(records):
            if str(r.get(key_field)) == str(key_value):
                row_index = i + 2  # +2 because row 1 is headers and sheet is 1-indexed
                break
        
        if row_index is None:
            logger.error(f"Record with {key_field}={key_value} not found in {sheet_name}")
            return False
        
        # Prepare cell updates
        updates = []
        for i, header in enumerate(headers):
            if header in record:
                value = record[header]
                cell = gspread.Cell(row_index, i + 1, value)
                updates.append(cell)
        
        # Update the cells
        if updates:
            worksheet.update_cells(updates)
            
            # Invalidate cache
            cache_key = f"{SHEET_ID}_{sheet_name}"
            if cache_key in _sheet_cache:
                del _sheet_cache[cache_key]
            
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error updating sheet data: {e}")
        return False

def append_sheet_data(sheet_name, records):
    """
    Append one or more records to a sheet.
    
    Args:
        sheet_name: Name of the sheet to append to
        records: List of dictionaries to append
        
    Returns:
        bool: Success or failure
    """
    try:
        client = _get_sheet_client()
        if not client:
            logger.error("Failed to get sheets client")
            return False
        
        # Open the spreadsheet and the specific worksheet
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get headers to ensure correct column order
        headers = worksheet.row_values(1)
        
        # Prepare rows to append
        rows = []
        for record in records:
            row = []
            for header in headers:
                value = record.get(header, '')
                row.append(value)
            rows.append(row)
        
        # Append rows
        if rows:
            worksheet.append_rows(rows)
            
            # Invalidate cache
            cache_key = f"{SHEET_ID}_{sheet_name}"
            if cache_key in _sheet_cache:
                del _sheet_cache[cache_key]
            
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error appending sheet data: {e}")
        return False

def get_stats():
    """
    Get game statistics for admin dashboard.
    
    Returns:
        dict: Game statistics
    """
    try:
        player_count = len(get_sheet_data(SHEET_NAMES['players']))
        alliance_count = len(get_sheet_data(SHEET_NAMES['alliances']))
        
        # In a full implementation, this would calculate more detailed stats
        
        return {
            'player_count': player_count,
            'alliance_count': alliance_count,
            'active_wars': 0,  # Placeholder
            'buildings_constructed': 0,  # Placeholder
            'units_trained': 0  # Placeholder
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {}
