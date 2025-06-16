"""
Sheets Helper: Google Sheets integration for SkyHustle.
"""
import os
import json
import base64
import datetime
import logging
from typing import Optional, Dict

import gspread
from google.oauth2.service_account import Credentials

# Load and authorize Google Sheets client
BASE64_CREDS = os.getenv("BASE64_CREDS")
if not BASE64_CREDS:
    raise RuntimeError("BASE64_CREDS is not set")

creds_info = json.loads(base64.b64decode(BASE64_CREDS))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("SHEET_ID is not set")

spreadsheet = gc.open_by_key(SHEET_ID)

# Worksheet tabs (must already exist with these exact names)
players_sheet      = spreadsheet.worksheet("Players")
inventory_sheet    = spreadsheet.worksheet("Inventory")
production_sheet   = spreadsheet.worksheet("ProductionRates")
caps_sheet         = spreadsheet.worksheet("StorageCaps")


async def load_player(player_id: str) -> Optional[Dict[str, str]]:
    """
    Load player info from the Players sheet.
    Returns {'player_id': str, 'name': str} or None if not found.
    """
    try:
        cell = players_sheet.find(player_id)
        row = players_sheet.row_values(cell.row)
        return {"player_id": row[0], "name": row[1]}
    except gspread.exceptions.CellNotFound:
        return None
    except Exception:
        logging.exception("Error loading player")
        return None


async def create_player(player_id: str, name: str) -> None:
    """
    Register a new player:
      1) Append to 'Players' sheet: player_id, name, created_at
      2) Initialize Inventory, ProductionRates & StorageCaps sheets with defaults
    """
    now_iso = datetime.datetime.utcnow().isoformat()

    # 1) Players
    players_sheet.append_row([player_id, name, now_iso])

    # 2) Default Inventory
    # Columns: player_id, wood, stone, gold, food, premium, last_update
    inventory_sheet.append_row([
        player_id,
        100,   # wood
        100,   # stone
        50,    # gold
        200,   # food
        0,     # premium
        now_iso
    ])

    # 3) Default ProductionRates
    # Columns: player_id, wood_rate, stone_rate, gold_rate, food_rate, premium_rate
    production_sheet.append_row([
        player_id,
        1.0,   # wood_rate/sec
        0.5,   # stone_rate/sec
        0.1,   # gold_rate/sec
        2.0,   # food_rate/sec
        0.0    # premium_rate/sec
    ])

    # 4) Default StorageCaps
    # Columns: player_id, wood_cap, stone_cap, gold_cap, food_cap, premium_cap
    caps_sheet.append_row([
        player_id,
        1000,  # wood_cap
        1000,  # stone_cap
        500,   # gold_cap
        2000,  # food_cap
        100    # premium_cap
    ]) 