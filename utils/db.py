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
inventory = sheet.worksheet("Inventory")


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
# ---------------------- ARMY SYSTEM ----------------------

def create_army(telegram_id):
    """Initialize an army for a new player."""
    try:
        army.append_row([
            str(telegram_id),
            0,  # Scouts
            0,  # Soldiers
            0,  # Tanks
            0   # Drones
        ])
        return True
    except Exception as e:
        print(f"Error creating army: {e}")
        return False

def get_army(telegram_id):
    """Fetch army details for a player."""
    try:
        ids = army.col_values(1)  # PlayerID column
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
    """Update army units for a player by adding deltas."""
    try:
        ids = army.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            current_data = get_army(telegram_id)
            if current_data:
                army.update_cell(row, 2, current_data['Scouts'] + scouts_delta)
                army.update_cell(row, 3, current_data['Soldiers'] + soldiers_delta)
                army.update_cell(row, 4, current_data['Tanks'] + tanks_delta)
                army.update_cell(row, 5, current_data['Drones'] + drones_delta)
                return True
    except Exception as e:
        print(f"Error updating army: {e}")
    return False
# ---------------------- RESEARCH SYSTEM ----------------------

def create_research(telegram_id):
    """Initialize research tree for a new player."""
    try:
        research.append_row([
            str(telegram_id),
            0,  # MiningSpeed
            0,  # ArmyStrength
            0,  # DefenseBoost
            0   # SpyPower
        ])
        return True
    except Exception as e:
        print(f"Error creating research: {e}")
        return False

def get_research(telegram_id):
    """Fetch research progress for a player."""
    try:
        ids = research.col_values(1)  # PlayerID column
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            values = research.row_values(row)
            return {
                "PlayerID": values[0],
                "MiningSpeed": int(values[1]),
                "ArmyStrength": int(values[2]),
                "DefenseBoost": int(values[3]),
                "SpyPower": int(values[4])
            }
        return None
    except Exception as e:
        print(f"Error getting research: {e}")
        return None

def update_research(telegram_id, mining_speed_delta=0, army_strength_delta=0, defense_boost_delta=0, spy_power_delta=0):
    """Update research tree for a player by adding deltas."""
    try:
        ids = research.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            current_data = get_research(telegram_id)
            if current_data:
                research.update_cell(row, 2, current_data['MiningSpeed'] + mining_speed_delta)
                research.update_cell(row, 3, current_data['ArmyStrength'] + army_strength_delta)
                research.update_cell(row, 4, current_data['DefenseBoost'] + defense_boost_delta)
                research.update_cell(row, 5, current_data['SpyPower'] + spy_power_delta)
                return True
    except Exception as e:
        print(f"Error updating research: {e}")
    return False

# ---------------------- ZONE CONTROL SYSTEM ----------------------

def claim_zone(telegram_id, zone_name):
    """Claim a zone for a player."""
    try:
        row = find_player(telegram_id)
        if row:
            player_profile.update_cell(row, 3, zone_name)  # Zone column
            return True
    except Exception as e:
        print(f"Error claiming zone: {e}")
    return False

def get_zone(telegram_id):
    """Get the current zone of a player."""
    try:
        player_data = get_player_data(telegram_id)
        if player_data:
            return player_data.get("Zone", "Unclaimed")
    except Exception as e:
        print(f"Error getting zone: {e}")
    return "Unclaimed"

def is_zone_claimed(zone_name):
    """Check if a zone is already claimed."""
    try:
        zones = player_profile.col_values(3)  # Zone column
        if zone_name in zones:
            return True
        return False
    except Exception as e:
        print(f"Error checking zone claim: {e}")
        return False
# ---------------------- INVENTORY SYSTEM ----------------------

def create_inventory(telegram_id):
    """Initialize an empty inventory for a new player."""
    try:
        inventory = sheet.worksheet("Inventory")
        inventory.append_row([
            str(telegram_id),  # TelegramID
            0, 0, 0, 0, 0      # Starting with 0 items for basicshield, revivekit, infinityscout, hazmatdrone, empdevice
        ])
        return True
    except Exception as e:
        print(f"Error creating inventory: {e}")
        return False

def get_inventory(telegram_id):
    """Fetch player's inventory row as a dictionary."""
    try:
        inventory = sheet.worksheet("Inventory")
        ids = inventory.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            values = inventory.row_values(row)
            headers = inventory.row_values(1)  # Header row
            return dict(zip(headers, values))
        return None
    except Exception as e:
        print(f"Error getting inventory: {e}")
        return None

def add_to_inventory(telegram_id, item_id, amount=1):
    """Add item(s) to a player's inventory."""
    try:
        inventory = sheet.worksheet("Inventory")
        ids = inventory.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            headers = inventory.row_values(1)

            if item_id not in headers:
                print(f"Item {item_id} not found in Inventory sheet headers!")
                return False

            col = headers.index(item_id) + 1
            current_amount = int(inventory.cell(row, col).value or 0)
            inventory.update_cell(row, col, current_amount + amount)
            return True
    except Exception as e:
        print(f"Error adding to inventory: {e}")
    return False

def use_from_inventory(telegram_id, item_id):
    """Consume (use) an item from inventory."""
    try:
        inventory = sheet.worksheet("Inventory")
        ids = inventory.col_values(1)
        if str(telegram_id) in ids:
            row = ids.index(str(telegram_id)) + 1
            headers = inventory.row_values(1)

            if item_id not in headers:
                print(f"Item {item_id} not found in Inventory sheet headers!")
                return False

            col = headers.index(item_id) + 1
            current_amount = int(inventory.cell(row, col).value or 0)

            if current_amount > 0:
                inventory.update_cell(row, col, current_amount - 1)
                return True
            else:
                return False
    except Exception as e:
        print(f"Error using item from inventory: {e}")
    return False
