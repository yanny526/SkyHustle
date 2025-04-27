import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import base64

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_data = os.getenv("GOOGLE_CREDS_BASE64")

if creds_data:
    creds_json = json.loads(base64.b64decode(creds_data))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
else:
    raise Exception("Missing Google credentials.")

# Connect to your Google Sheet
SHEET_NAME = "SkyHustleSheet"  # Make sure your Google Sheet is named this!
sheet = client.open(SHEET_NAME)

# Load the necessary tabs
player_profile = sheet.worksheet("PlayerProfile")
army = sheet.worksheet("Army")
buildings = sheet.worksheet("Buildings")
research = sheet.worksheet("Research")
missions = sheet.worksheet("Missions")


# Utility Functions

def find_player(telegram_id):
    """Find a player row by Telegram ID. Returns row number if found, else None."""
    try:
        ids = player_profile.col_values(2)  # TelegramID column
        if str(telegram_id) in ids:
            return ids.index(str(telegram_id)) + 1  # +1 because Sheets are 1-indexed
        return None
    except Exception as e:
        print(f"Error finding player: {e}")
        return None

def create_player(telegram_id, player_name):
    """Create a new player if not already existing."""
    if not find_player(telegram_id):
        player_profile.append_row([
            player_name, 
            str(telegram_id), 
            "Unclaimed",  # Zone
            1000,  # Gold
            500,   # Stone
            300,   # Iron
            100,   # Energy
            0,     # ArmySize
            "No",  # ShieldActive
            "",    # LastDailyClaim
            "",    # LastMineAction
            ""     # LastAttackAction
        ])
        return True
    return False

def get_player_data(telegram_id):
    """Fetch all player data."""
    row = find_player(telegram_id)
    if row:
        values = player_profile.row_values(row)
        return {
            "PlayerName": values[0],
            "TelegramID": values[1],
            "Zone": values[2],
            "Gold": int(values[3]),
            "Stone": int(values[4]),
            "Iron": int(values[5]),
            "Energy": int(values[6]),
            "ArmySize": int(values[7]),
            "ShieldActive": values[8]
        }
    return None

def update_player_resources(telegram_id, gold_delta=0, stone_delta=0, iron_delta=0, energy_delta=0):
    """Update player's resources by adding deltas."""
    row = find_player(telegram_id)
    if row:
        # Get current values
        current_data = get_player_data(telegram_id)
        if current_data:
            player_profile.update_cell(row, 4, current_data['Gold'] + gold_delta)
            player_profile.update_cell(row, 5, current_data['Stone'] + stone_delta)
            player_profile.update_cell(row, 6, current_data['Iron'] + iron_delta)
            player_profile.update_cell(row, 7, current_data['Energy'] + energy_delta)
            return True
    return False
