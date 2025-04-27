# utils/google_sheets.py
import json
import os
import base64

import gspread
from google.oauth2.service_account import Credentials

SHEET_URL = "YOUR_SHEET_URL"  # Replace with your sheet URL
WORKSHEET_NAME = "SkyHustle"  # Replace with your worksheet name

def get_sheet():
    """Connects to the Google Sheet."""
    try:
        creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_BASE64")).decode("utf-8")
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        return client.open_by_url(SHEET_URL).worksheet(WORKSHEET_NAME)
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def get_all_players(sheet):
    """Fetches all player data from the sheet and returns a list of Player objects."""
    from core.player import Player  # Import here to avoid circular dependency
    try:
        records = sheet.get_all_records()
        return [Player.from_dict(row) for row in records]
    except Exception as e:
        print(f"Error fetching all players: {e}")
        return []

def find_player_by_chat_id(sheet, chat_id):
    """Finds a player by their chat ID."""
    players = get_all_players(sheet)
    for player in players:
        if player.chat_id == chat_id:
            return player
    return None

def find_player_by_name(sheet, name):
    """Finds a player by their name (alias)."""
    players = get_all_players(sheet)
    for player in players:
        if player.name.lower() == name.lower():
            return player
    return None

def save_player(sheet, player):
    """Saves a player's data back to the Google Sheet."""
    player_data = player.to_dict()
    row_data = [
        player_data.get("ChatID"),
        player_data.get("Name"),
        player_data.get("Ore"),
        player_data.get("Energy"),
        player_data.get("Credits"),
        player_data.get("Army"),
        player_data.get("Zone"),
        player_data.get("ShieldUntil"),
        player_data.get("DailyStreak"),
        player_data.get("LastDaily"),
        player_data.get("BlackMarketUnlocked"),
        player_data.get("Items"),
        player_data.get("Missions"),
        player_data.get("LastMissionReset"),
        player_data.get("Wins"),
        player_data.get("Losses"),
        player_data.get("Banner"),
        player_data.get("RefineryLevel"),
        player_data.get("LabLevel"),
        player_data.get("DefenseLevel"),
        player_data.get("Research"),
        player_data.get("Faction"),
    ]

    try:
        if "_row" in player_data and player_data["_row"]:
            row_number = int(player_data["_row"])
            sheet.update(f"A{row_number}:V{row_number}", [row_data])
        else:
            # Handle new player save (append)
            new_row = row_data
            sheet.append_row(new_row)
            # Update the player's row number after appending (less efficient, but works)
            #  This is tricky, you might need to rethink how you track row numbers
            #  A better approach might be to reload the player after appending
            #  Or to maintain a local cache of row numbers
            #  For now, we'll leave it simple, but be aware of the inefficiency
    except Exception as e:
        print(f"Error saving player {player.name}: {e}")

def create_new_player(sheet, chat_id):
    """Creates a new player in the Google Sheet."""
    from core.player import Player  # Import here to avoid circular dependency

    new_player = Player(chat_id=chat_id)  # Create a new Player object
    save_player(sheet, new_player)  # Save it to the sheet

    #  Inefficiently retrieve the player with the row number
    #  This is a temporary workaround
    return find_player_by_chat_id(sheet, chat_id)

def find_or_create_player(sheet, chat_id):
    """Finds a player by chat ID, or creates a new one if not found."""
    player = find_player_by_chat_id(sheet, chat_id)
    if not player:
        player = create_new_player(sheet, chat_id)
    return player
