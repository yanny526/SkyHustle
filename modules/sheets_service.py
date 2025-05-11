"""
Sheets service module for the SkyHustle Telegram bot.
Handles all interactions with Google Sheets API.
"""
import os
import json
import logging
import asyncio
import base64
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# Sheets cache to reduce API calls
_sheets_cache = {}
_cache_expires = {}
_cache_ttl = 300  # 5 minutes

async def get_credentials() -> Credentials:
    """
    Get Google API credentials from environment variable.
    
    Returns:
        Credentials object for Google API
    """
    try:
        base64_creds = os.getenv("BASE64_CREDS")
        if not base64_creds:
            raise ValueError("BASE64_CREDS environment variable not set")
        
        # Decode base64 credentials
        creds_json = base64.b64decode(base64_creds).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        # Create credentials from service account info
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        return credentials
    
    except Exception as e:
        logging.error(f"Error getting credentials: {e}", exc_info=True)
        raise

async def get_sheet_id() -> str:
    """
    Get Google Sheet ID from environment variable.
    
    Returns:
        Google Sheet ID
    """
    sheet_id = os.getenv("SHEET_ID")
    if not sheet_id:
        raise ValueError("SHEET_ID environment variable not set")
    
    return sheet_id

async def get_client() -> gspread.Client:
    """
    Get authorized Google Sheets client.
    
    Returns:
        Authorized gspread client
    """
    credentials = await get_credentials()
    client = gspread.authorize(credentials)
    return client

async def get_spreadsheet():
    """
    Get the SkyHustle spreadsheet.
    
    Returns:
        gspread Spreadsheet object
    """
    client = await get_client()
    sheet_id = await get_sheet_id()
    
    # Use run_in_executor for blocking API calls
    loop = asyncio.get_event_loop()
    spreadsheet = await loop.run_in_executor(None, lambda: client.open_by_key(sheet_id))
    
    return spreadsheet

async def get_sheet(sheet_name: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get a specific worksheet from the spreadsheet.
    
    Args:
        sheet_name: Name of the worksheet
        force_refresh: Whether to force a refresh from the API
    
    Returns:
        Dictionary with sheet values
    """
    global _sheets_cache, _cache_expires
    
    now = datetime.now().timestamp()
    
    # Check if sheet is in cache and not expired
    if (not force_refresh and 
        sheet_name in _sheets_cache and 
        sheet_name in _cache_expires and 
        _cache_expires[sheet_name] > now):
        return _sheets_cache[sheet_name]
    
    try:
        spreadsheet = await get_spreadsheet()
        
        # Use run_in_executor for blocking API calls
        loop = asyncio.get_event_loop()
        
        # Try to get the worksheet
        try:
            worksheet = await loop.run_in_executor(None, lambda: spreadsheet.worksheet(sheet_name))
        except gspread.exceptions.WorksheetNotFound:
            # Worksheet doesn't exist, create it
            worksheet = await loop.run_in_executor(None, lambda: spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20))
            
            # Add header row based on sheet type
            header_row = get_header_row(sheet_name)
            if header_row:
                await loop.run_in_executor(None, lambda: worksheet.update('A1', [header_row]))
        
        # Get all values from the worksheet
        values = await loop.run_in_executor(None, lambda: worksheet.get_all_values())
        
        # Create sheet data object
        sheet_data = {
            "name": sheet_name,
            "values": values
        }
        
        # Update cache
        _sheets_cache[sheet_name] = sheet_data
        _cache_expires[sheet_name] = now + _cache_ttl
        
        return sheet_data
    
    except Exception as e:
        logging.error(f"Error getting sheet {sheet_name}: {e}", exc_info=True)
        
        # If sheet is in cache, return cached version even if expired
        if sheet_name in _sheets_cache:
            logging.warning(f"Returning expired cache for sheet {sheet_name}")
            return _sheets_cache[sheet_name]
        
        # Return empty sheet
        return {
            "name": sheet_name,
            "values": []
        }

def get_header_row(sheet_name: str) -> List[str]:
    """
    Get header row for a sheet based on its name.
    
    Args:
        sheet_name: Name of the sheet
    
    Returns:
        List of column headers
    """
    headers = {
        "Players": ["player_id", "display_name", "credits", "minerals", "energy", "skybucks", "experience", "tutorial_completed", "tutorial_state", "last_login"],
        "Buildings": ["building_id", "player_id", "level", "position_x", "position_y"],
        "Units": ["unit_id", "player_id", "quantity", "level"],
        "Research": ["tech_id", "player_id", "level", "completed_at"],
        "BuildQueue": ["queue_id", "player_id", "building_id", "start_time", "end_time", "quantity", "completed"],
        "TrainingQueue": ["queue_id", "player_id", "unit_id", "start_time", "end_time", "quantity", "completed"],
        "Alliances": ["alliance_id", "name", "leader_id", "join_code", "created_at", "member_count", "power_ranking"],
        "AllianceMembers": ["player_id", "alliance_id", "joined_at", "role"],
        "Battles": ["battle_id", "attacker_id", "defender_id", "attacker_units", "defender_units", "result", "resources_gained", "timestamp"],
        "Events": ["event_id", "name", "description", "start_time", "end_time", "requirements", "rewards"]
    }
    
    return headers.get(sheet_name, [])

async def update_sheet_row(sheet_name: str, row_index: int, values: List[Any]) -> None:
    """
    Update a row in a sheet.
    
    Args:
        sheet_name: Name of the sheet
        row_index: 1-based index of the row
        values: List of values to update
    """
    try:
        spreadsheet = await get_spreadsheet()
        
        # Use run_in_executor for blocking API calls
        loop = asyncio.get_event_loop()
        
        # Get the worksheet
        worksheet = await loop.run_in_executor(None, lambda: spreadsheet.worksheet(sheet_name))
        
        # Update the row
        # Convert values to strings
        string_values = [str(val) for val in values]
        await loop.run_in_executor(None, lambda: worksheet.update(f'A{row_index}', [string_values]))
        
        # Clear cache for this sheet
        if sheet_name in _sheets_cache:
            del _sheets_cache[sheet_name]
        if sheet_name in _cache_expires:
            del _cache_expires[sheet_name]
    
    except Exception as e:
        logging.error(f"Error updating row {row_index} in sheet {sheet_name}: {e}", exc_info=True)
        raise

async def append_sheet_row(sheet_name: str, values: List[Any]) -> int:
    """
    Append a row to a sheet.
    
    Args:
        sheet_name: Name of the sheet
        values: List of values to append
    
    Returns:
        The 1-based index of the new row
    """
    try:
        spreadsheet = await get_spreadsheet()
        
        # Use run_in_executor for blocking API calls
        loop = asyncio.get_event_loop()
        
        # Get the worksheet
        worksheet = await loop.run_in_executor(None, lambda: spreadsheet.worksheet(sheet_name))
        
        # Convert values to strings
        string_values = [str(val) for val in values]
        
        # Append the row
        result = await loop.run_in_executor(None, lambda: worksheet.append_row(string_values))
        
        # Clear cache for this sheet
        if sheet_name in _sheets_cache:
            del _sheets_cache[sheet_name]
        if sheet_name in _cache_expires:
            del _cache_expires[sheet_name]
        
        # Get the new row index
        new_row_index = result['updates']['updatedRange'].split(':')[0]
        row_num = int(''.join(filter(str.isdigit, new_row_index)))
        
        return row_num
    
    except Exception as e:
        logging.error(f"Error appending row to sheet {sheet_name}: {e}", exc_info=True)
        raise

async def find_row_by_col_value(sheet: Dict[str, Any], value: str, col_index: int) -> Tuple[Optional[int], Optional[List[str]]]:
    """
    Find a row in a sheet by a column value.
    
    Args:
        sheet: Sheet data object
        value: Value to find
        col_index: Index of the column to search in
    
    Returns:
        Tuple of (row_index, row) or (None, None) if not found
    """
    if not sheet["values"]:
        return None, None
    
    # Skip header row
    for i, row in enumerate(sheet["values"][1:], 1):
        if len(row) > col_index and row[col_index] == value:
            return i + 1, row  # +1 for header row and 1-based indexing
    
    return None, None

async def clear_sheet(sheet_name: str) -> None:
    """
    Clear all data from a sheet except the header row.
    
    Args:
        sheet_name: Name of the sheet
    """
    try:
        spreadsheet = await get_spreadsheet()
        
        # Use run_in_executor for blocking API calls
        loop = asyncio.get_event_loop()
        
        # Get the worksheet
        worksheet = await loop.run_in_executor(None, lambda: spreadsheet.worksheet(sheet_name))
        
        # Get header row
        header_row = get_header_row(sheet_name)
        
        # Clear the sheet
        await loop.run_in_executor(None, lambda: worksheet.clear())
        
        # Add header row back
        if header_row:
            await loop.run_in_executor(None, lambda: worksheet.update('A1', [header_row]))
        
        # Clear cache for this sheet
        if sheet_name in _sheets_cache:
            del _sheets_cache[sheet_name]
        if sheet_name in _cache_expires:
            del _cache_expires[sheet_name]
    
    except Exception as e:
        logging.error(f"Error clearing sheet {sheet_name}: {e}", exc_info=True)
        raise
