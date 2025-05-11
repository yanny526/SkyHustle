"""
Google Sheets service for SkyHustle.
Provides utility functions for interacting with Google Sheets.
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound
from google.oauth2.service_account import Credentials

from config import SHEET_ID, get_google_creds, SHEET_NAMES

# Cache for spreadsheet objects
_spreadsheet_cache = {}
_worksheet_cache = {}

async def get_spreadsheet():
    """
    Get the Google Spreadsheet object.
    
    Returns:
        gspread.Spreadsheet: The Google Spreadsheet
    """
    global _spreadsheet_cache
    
    # Check if spreadsheet is in cache
    if SHEET_ID in _spreadsheet_cache:
        return _spreadsheet_cache[SHEET_ID]
    
    try:
        # Get credentials
        creds_dict = get_google_creds()
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Authenticate and get spreadsheet
        gc = gspread.authorize(creds)
        # Ensure SHEET_ID is not None
        sheet_id = SHEET_ID
        if not sheet_id:
            raise ValueError("SHEET_ID is not set")
        spreadsheet = gc.open_by_key(sheet_id)
        
        # Cache the spreadsheet
        _spreadsheet_cache[SHEET_ID] = spreadsheet
        
        return spreadsheet
        
    except Exception as e:
        logging.error(f"Error getting spreadsheet: {e}", exc_info=True)
        raise

async def get_sheet(sheet_name: str):
    """
    Get a specific worksheet from the Google Spreadsheet.
    
    Args:
        sheet_name: Name of the worksheet
    
    Returns:
        gspread.Worksheet: The worksheet
    """
    global _worksheet_cache
    
    # Check if worksheet is in cache
    cache_key = f"{SHEET_ID}:{sheet_name}"
    if cache_key in _worksheet_cache:
        return _worksheet_cache[cache_key]
    
    try:
        # Get spreadsheet
        spreadsheet = await get_spreadsheet()
        
        # Get worksheet
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Cache the worksheet
        _worksheet_cache[cache_key] = worksheet
        
        return worksheet
        
    except Exception as e:
        logging.error(f"Error getting worksheet '{sheet_name}': {e}", exc_info=True)
        raise

async def find_row_by_col_value(sheet_name: str, col_idx: int, value: str) -> Tuple[Optional[int], Optional[List[str]]]:
    """
    Find a row in a worksheet by the value in a specific column.
    
    Args:
        sheet_name: Name of the worksheet
        col_idx: Index of the column to search (0-based)
        value: Value to search for
    
    Returns:
        Tuple of (row_index, row_data) or (None, None) if not found
    """
    try:
        # Get worksheet
        worksheet = await get_sheet(sheet_name)
        
        # Get all values
        all_values = worksheet.get_all_values()
        
        # Skip header row
        for i, row in enumerate(all_values[1:], start=2):
            if str(row[col_idx]) == str(value):
                return (i, row)
        
        return (None, None)
        
    except Exception as e:
        logging.error(f"Error finding row in '{sheet_name}': {e}", exc_info=True)
        return (None, None)

async def update_row(sheet_name: str, row_idx: int, values: List[Any]) -> bool:
    """
    Update a row in a worksheet.
    
    Args:
        sheet_name: Name of the worksheet
        row_idx: Index of the row to update (1-based)
        values: List of values to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get worksheet
        worksheet = await get_sheet(sheet_name)
        
        # Update the row
        cell_range = f'A{row_idx}:Z{row_idx}'
        worksheet.update(cell_range, [values])
        
        return True
        
    except Exception as e:
        logging.error(f"Error updating row in '{sheet_name}': {e}", exc_info=True)
        return False

async def append_row(sheet_name: str, values: List[Any]) -> bool:
    """
    Append a row to a worksheet.
    
    Args:
        sheet_name: Name of the worksheet
        values: List of values to append
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get worksheet
        worksheet = await get_sheet(sheet_name)
        
        # Append the row
        worksheet.append_row(values)
        
        return True
        
    except Exception as e:
        logging.error(f"Error appending row to '{sheet_name}': {e}", exc_info=True)
        return False

async def get_all_rows(sheet_name: str) -> List[List[str]]:
    """
    Get all rows from a worksheet.
    
    Args:
        sheet_name: Name of the worksheet
    
    Returns:
        List of rows (each row is a list of values)
    """
    try:
        # Get worksheet
        worksheet = await get_sheet(sheet_name)
        
        # Get all values
        all_values = worksheet.get_all_values()
        
        # Skip header row
        return all_values[1:]
        
    except Exception as e:
        logging.error(f"Error getting all rows from '{sheet_name}': {e}", exc_info=True)
        return []

async def initialize_sheets() -> bool:
    """
    Initialize all required worksheets if they don't exist.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get spreadsheet
        spreadsheet = await get_spreadsheet()
        
        # Get existing worksheet titles
        existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
        
        # Create worksheets that don't exist
        for sheet_name in SHEET_NAMES.values():
            if sheet_name not in existing_sheets:
                logging.info(f"Creating worksheet '{sheet_name}'")
                
                # Create the worksheet
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                
                # Add headers based on sheet type
                header_row = []
                if sheet_name == SHEET_NAMES["players"]:
                    header_row = [
                        "player_id", "display_name", "credits", "minerals", "energy", 
                        "skybucks", "experience", "level", "tutorial_completed", 
                        "last_login", "daily_streak", "last_daily", "alliance_id"
                    ]
                elif sheet_name == SHEET_NAMES["buildings"]:
                    header_row = [
                        "player_id", "building_id", "building_type", "level", "quantity", 
                        "build_started", "build_completed"
                    ]
                elif sheet_name == SHEET_NAMES["units"]:
                    header_row = [
                        "player_id", "unit_id", "unit_type", "level", "quantity", 
                        "train_started", "train_completed"
                    ]
                elif sheet_name == SHEET_NAMES["research"]:
                    header_row = [
                        "player_id", "tech_id", "tech_name", "level", 
                        "research_started", "research_completed"
                    ]
                elif sheet_name == SHEET_NAMES["alliances"]:
                    header_row = [
                        "alliance_id", "alliance_name", "leader_id", "created_date", 
                        "description", "members_count", "power"
                    ]
                elif sheet_name == SHEET_NAMES["battles"]:
                    header_row = [
                        "battle_id", "attacker_id", "defender_id", "timestamp", 
                        "attacker_units", "defender_units", "outcome", "rewards"
                    ]
                
                # Update the header row
                if header_row:
                    worksheet.update("A1", [header_row])
                
                # Add to cache
                cache_key = f"{SHEET_ID}:{sheet_name}"
                _worksheet_cache[cache_key] = worksheet
        
        return True
        
    except Exception as e:
        logging.error(f"Error initializing sheets: {e}", exc_info=True)
        return False

async def get_sheet_stats() -> Dict[str, int]:
    """
    Get basic statistics from each sheet.
    
    Returns:
        Dict with stats (players count, alliances count, etc.)
    """
    stats = {
        "players": 0,
        "alliances": 0,
        "battles": 0,
    }
    
    try:
        # Get player count
        players = await get_all_rows(SHEET_NAMES["players"])
        stats["players"] = len(players)
        
        # Get alliance count
        alliances = await get_all_rows(SHEET_NAMES["alliances"])
        stats["alliances"] = len(alliances)
        
        # Get battle count today
        battles = await get_all_rows(SHEET_NAMES["battles"])
        today = datetime.now().strftime("%Y-%m-%d")
        today_battles = [b for b in battles if b[3].startswith(today)]
        stats["battles"] = len(today_battles)
        
        return stats
        
    except Exception as e:
        logging.error(f"Error getting sheet stats: {e}", exc_info=True)
        return stats

async def get_recent_activity(limit: int = 10) -> List[Dict[str, str]]:
    """
    Get recent activity from battles and other events.
    
    Args:
        limit: Maximum number of activities to return
    
    Returns:
        List of activity dictionaries
    """
    activities = []
    
    try:
        # Get recent battles
        battles = await get_all_rows(SHEET_NAMES["battles"])
        
        # Sort by timestamp (descending)
        battles.sort(key=lambda b: b[3], reverse=True)
        
        # Get player names
        player_rows = await get_all_rows(SHEET_NAMES["players"])
        player_map = {row[0]: row[1] for row in player_rows}
        
        # Create activity entries
        for battle in battles[:limit]:
            battle_id = battle[0]
            attacker_id = battle[1]
            defender_id = battle[2]
            timestamp = battle[3]
            outcome = battle[6]
            
            attacker_name = player_map.get(attacker_id, f"Player {attacker_id}")
            defender_name = player_map.get(defender_id, f"Player {defender_id}")
            
            activities.append({
                "time": timestamp,
                "player": attacker_name,
                "action": "Attack",
                "details": f"{outcome} against {defender_name}"
            })
            
        return activities[:limit]
        
    except Exception as e:
        logging.error(f"Error getting recent activity: {e}", exc_info=True)
        return []