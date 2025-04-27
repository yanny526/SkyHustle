# utils/db.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import base64

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_data = os.getenv("GOOGLE_CREDS_BASE64")

if creds_data:
    creds_json = json.loads(base64.b64decode(creds_data))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
else:
    raise Exception("Missing Google credentials.")

SHEET_NAME = "SkyHustleSheet"
sheet = client.open(SHEET_NAME)

# Load worksheets
player_profile = sheet.worksheet("PlayerProfile")
army = sheet.worksheet("Army")
buildings = sheet.worksheet("Buildings")
research = sheet.worksheet("Research")
missions = sheet.worksheet("Missions")
inventory = sheet.worksheet("Inventory")

# ---------------------- PLAYER SYSTEM ----------------------

def find_player(telegram_id):
    try:
        ids = player_profile.col_values(2)
        if str(telegram_id) in ids:
            return ids.index(str(telegram_id)) + 1
        return None
    except Exception as e:
        print(f"Error finding player: {e}")
        return None

def create_player(telegram_id, player_name):
    if not find_player(telegram_id):
        player_profile.append_row([
            player_name,
            str(telegram_id),
            "Unclaimed",
            1000,
            500,
            300,
            100,
            0,
            "No",
            "",
            "",
            ""
        ])
        inventory.append_row([str(telegram_id), 0, 0, 0, 0, 0])
        return True
    return False

def get_player_data(telegram_id):
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
    row = find_player(telegram_id)
    if row:
        current = get_player_data(telegram_id)
        if current:
            player_profile.update_cell(row, 4, current["Gold"] + gold_delta)
            player_profile.update_cell(row, 5, current["Stone"] + stone_delta)
            player_profile.update_cell(row, 6, current["Iron"] + iron_delta)
            player_profile.update_cell(row, 7, current["Energy"] + energy_delta)
            return True
    return False

# ---------------------- ARMY SYSTEM ----------------------

def create_army(telegram_id):
    try:
        army.append_row([str(telegram_id), 0, 0, 0, 0])
        return True
    except Exception as e:
        print(f"Error creating army: {e}")
        return False

def get_army(telegram_id):
    try:
        ids = army.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            values = army.row_values(row)
            return {
                "PlayerID": values[0],
                "Scouts": int(values[1]),
                "Soldiers": int(values[2]),
                "Tanks": int(values[3]),
                "Drones": int(values[4])
            }
        return None
    except Exception as e:
        print(f"Error getting army: {e}")
        return None

def update_army(telegram_id, scouts_delta=0, soldiers_delta=0, tanks_delta=0, drones_delta=0):
    try:
        ids = army.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            current = get_army(telegram_id)
            if current:
                army.update_cell(row, 2, current["Scouts"] + scouts_delta)
                army.update_cell(row, 3, current["Soldiers"] + soldiers_delta)
                army.update_cell(row, 4, current["Tanks"] + tanks_delta)
                army.update_cell(row, 5, current["Drones"] + drones_delta)
                return True
    except Exception as e:
        print(f"Error updating army: {e}")
    return False

# ---------------------- ZONE CONTROL SYSTEM ----------------------

def claim_zone(telegram_id, zone_name):
    try:
        row = find_player(telegram_id)
        if row:
            player_profile.update_cell(row, 3, zone_name)
            return True
    except Exception as e:
        print(f"Error claiming zone: {e}")
    return False

def get_zone(telegram_id):
    try:
        player_data = get_player_data(telegram_id)
        if player_data:
            return player_data.get("Zone", "Unclaimed")
    except Exception as e:
        print(f"Error getting zone: {e}")
    return "Unclaimed"

def is_zone_claimed(zone_name):
    try:
        zones = player_profile.col_values(3)
        return zone_name in zones
    except Exception as e:
        print(f"Error checking zone claim: {e}")
        return False

# ---------------------- INVENTORY SYSTEM ----------------------

def get_inventory(telegram_id):
    try:
        ids = inventory.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            headers = inventory.row_values(1)
            values = inventory.row_values(row)
            return dict(zip(headers, values))
        return None
    except Exception as e:
        print(f"Error getting inventory: {e}")
        return None

def add_to_inventory(telegram_id, item_id, amount=1):
    try:
        ids = inventory.col_values(1)
        if str(telegram_id) not in ids:
            # If player does not exist, create their row
            inventory.append_row([str(telegram_id)] + [0] * (len(inventory.row_values(1)) - 1))
            ids = inventory.col_values(1)  # Refresh ids

        row = ids.index(str(telegram_id)) + 1
        headers = inventory.row_values(1)
        if item_id not in headers:
            print(f"Item {item_id} not found in inventory sheet.")
            return False

        col = headers.index(item_id) + 1
        current_qty = int(inventory.cell(row, col).value or 0)
        inventory.update_cell(row, col, current_qty + amount)
        return True
    except Exception as e:
        print(f"Error adding to inventory: {e}")
    return False

def remove_from_inventory(telegram_id, item_id):
    try:
        ids = inventory.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            headers = inventory.row_values(1)
            if item_id not in headers:
                return False
            col = headers.index(item_id) + 1
            current_qty = int(inventory.cell(row, col).value or 0)
            if current_qty > 0:
                inventory.update_cell(row, col, current_qty - 1)
                return True
    except Exception as e:
        print(f"Error removing from inventory: {e}")
    return False

def has_item(telegram_id, item_id):
    try:
        ids = inventory.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            headers = inventory.row_values(1)
            if item_id not in headers:
                return False
            col = headers.index(item_id) + 1
            qty = int(inventory.cell(row, col).value or 0)
            return qty > 0
    except Exception as e:
        print(f"Error checking inventory: {e}")
    return False
