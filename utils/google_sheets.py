
# google_sheets.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheet Setup
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"
ARMY_SHEET_NAME = "army"

# Authorize connection
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open army worksheet
sheet = client.open_by_key(SHEET_ID)
army_ws = sheet.worksheet(ARMY_SHEET_NAME)

# Load player's army
def load_player_army(player_id):
    try:
        records = army_ws.get_all_records()
        player_army = {}

        for row in records:
            if str(row['player_id']) == str(player_id):
                player_army[row['unit_name']] = int(row['quantity'])

        return player_army
    except Exception as e:
        print(f"Error loading player army: {e}")
        return {}

# Save player's army
def save_player_army(player_id, army_data):
    try:
        # First delete old entries for this player
        records = army_ws.get_all_records()
        cell_list = army_ws.findall(str(player_id))

        for cell in cell_list:
            if army_ws.cell(cell.row, 1).value == str(player_id):
                army_ws.delete_row(cell.row)

        # Now insert updated army data
        for unit_name, quantity in army_data.items():
            if quantity > 0:
                army_ws.append_row([player_id, unit_name, quantity])

    except Exception as e:
        print(f"Error saving player army: {e}")
