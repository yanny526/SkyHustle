import os
import base64
import json
import datetime
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials
from gspread import WorksheetNotFound
from gspread.exceptions import GSpreadException

# ------------------------------------------------------------------------------
# Module-level variables
# ------------------------------------------------------------------------------
_gc = None            # type: gspread.Client
_sheet = None         # type: gspread.Spreadsheet
_players_ws = None    # type: gspread.Worksheet

def get_sheet(sheet_title: str) -> Optional[gspread.Worksheet]:
    """Retrieves a worksheet by its title, creating it if it doesn't exist."""
    global _sheet # Ensure _sheet is accessible
    if _sheet is None:
        raise RuntimeError("Spreadsheet not initialized. Call initialize_sheets() first.")
    try:
        return _sheet.worksheet(sheet_title)
    except gspread.exceptions.WorksheetNotFound:
        # Create the worksheet if it doesn't exist
        new_ws = _sheet.add_worksheet(title=sheet_title, rows="100", cols="20") # Default size
        # Add a header row for basic identification if needed, or leave empty
        if sheet_title == "pending_upgrades":
            new_ws.append_row(["id", "user_id", "building_key", "new_level", "finish_at"])
        return new_ws

# Define all possible headers that might be needed
needed_headers = [
    # Basic player info
    "user_id", "telegram_username", "game_name",
    "coord_x", "coord_y",
    
    # Resources
    "resources_wood", "resources_stone", "resources_food", 
    "resources_gold", "resources_energy", "resources_diamonds",
    "gold_balance", "wood_balance", "research_balance", # New balance fields
    
    # Capacities
    "capacity_gold", "capacity_wood", "capacity_research", # New capacity fields
    
    # Rates (per hour)
    "gold_rate", "wood_rate", "research_rate", # New rate fields
    
    # Buildings
    "base_level", "mine_level", "lumber_house_level", 
    "warehouse_level", "barracks_level", "power_plant_level",
    "hospital_level", "research_lab_level", "workshop_level", 
    "jail_level",
    
    # Stats
    "power", "prestige_level",
    
    # Alliance
    "alliance_name", "alliance_role", "alliance_joined_at",
    "alliance_members_count", "alliance_power", "zones_controlled",
    
    # Army
    "army_infantry", "army_tank", "army_artillery", "army_destroyer",
    "army_bm_barrage", "army_venom_reaper", "army_titan_crusher",
    "army_dead_infantry", "army_dead_tanks",
    
    # Black Market Items
    "items_hazmat_mask", "items_energy_drink", "items_repair_kit",
    "items_medkit", "items_radar", "items_shield_generator",
    "items_revive_all", "items_emp_device", "items_hazmat_drone",
    "items_infinite_scout", "items_speedup_1h", "items_shield_adv",
    
    # Timers
    "timers_base_level", "timers_mine_level", "timers_lumber_level",
    "timers_warehouse_level", "timers_barracks_level", "timers_power_level",
    "timers_hospital_level", "timers_research_level", "timers_workshop_level",
    "timers_jail_level", "timers_emp_boost_end", "timers_hazmat_access_end", # New timer fields
    
    # Zone Control
    "scheduled_zone", "scheduled_time", "controlled_zone",
    
    # Misc
    "energy", "energy_max", "last_daily", "last_attack", "last_collection"
]

# Required OAuth scopes for reading/writing Google Sheets & Drive
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _authenticate_and_open_sheet() -> None:
    """Authenticate to Google Sheets using BASE64_CREDS and open the spreadsheet."""
    global _gc, _sheet

    raw_creds = os.getenv("BASE64_CREDS")
    sheet_id = os.getenv("SHEET_ID")
    if not raw_creds or not sheet_id:
        raise RuntimeError("BASE64_CREDS and SHEET_ID must be set in environment variables.")

    try:
        creds_json = json.loads(raw_creds) if raw_creds.strip().startswith("{") else json.loads(base64.b64decode(raw_creds))
    except Exception as e:
        raise RuntimeError(f"Failed to parse BASE64_CREDS as JSON or base64: {e}")

    credentials = Credentials.from_service_account_info(creds_json, scopes=_SCOPES)
    _gc = gspread.authorize(credentials)
    _sheet = _gc.open_by_key(sheet_id)

def _ensure_players_worksheet() -> None:
    """Ensure that the "Players" worksheet exists with the correct headers."""
    global _players_ws

    try:
        _players_ws = _sheet.worksheet("Players")
    except gspread.exceptions.WorksheetNotFound:
        _players_ws = _sheet.add_worksheet(title="Players", rows="100", cols=str(len(needed_headers)))
        _players_ws.append_row(needed_headers)
        return

    existing = _players_ws.row_values(1)
    to_append = [h for h in needed_headers if h not in existing]
    if to_append:
        updated_headers = existing + to_append
        _players_ws.update('A1', [updated_headers])

def initialize_sheets() -> None:
    """Initialize Google Sheets client and ensure the Players worksheet exists."""
    if _gc and _sheet and _players_ws:
        return
    _authenticate_and_open_sheet()
    _ensure_players_worksheet()

def get_player_row(user_id: int) -> Optional[int]:
    """Return the row number where user_id matches, or None if not found."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    print(f"DEBUG: get_player_row - Searching for user_id: {user_id}")
    try:
        # It's crucial that user_id in the sheet is treated consistently.
        # If stored as numbers, gspread.find might struggle with string search.
        # We will try to find it as a string first.
        cell = _players_ws.find(str(user_id), in_column=1)
        if cell:
            print(f"DEBUG: get_player_row - Found user_id {user_id} at row: {cell.row}")
            return cell.row
        else:
            # If not found as string, try iterating and converting to int for comparison
            # This is a fallback and can be slow for large sheets.
            all_user_ids = _players_ws.col_values(1)[1:] # Skip header row
            print(f"DEBUG: get_player_row - User ID not found as string, checking all_user_ids: {all_user_ids}")
            for idx, sheet_user_id_str in enumerate(all_user_ids):
                try:
                    if int(sheet_user_id_str) == user_id:
                        found_row = idx + 2 # +1 for 0-index to 1-index, +1 for header row
                        print(f"DEBUG: get_player_row - Found user_id {user_id} via int conversion at row: {found_row}")
                        return found_row
                except ValueError:
                    continue # Skip if not a valid integer
            print(f"DEBUG: get_player_row - User ID {user_id} not found in sheet.")
            return None
    except GSpreadException as e:
        print(f"ERROR: get_player_row - GSpreadException: {e}")
        return None

def create_new_player(user_id: int, telegram_username: str, game_name: str) -> None:
    """Append a new player row with default resources, levels, and coordinates."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    if get_player_row(user_id) is not None:
        raise ValueError(f"User ID {user_id} already exists.")

    coord_x = random.randint(1, 1000)
    coord_y = random.randint(1, 1000)
    iso_now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    new_row = [
        user_id,
        telegram_username or "",
        game_name,
        coord_x,
        coord_y,
        1000,  # resources_wood
        1000,  # resources_stone
        500,   # resources_gold
        500,   # resources_food
        1000,     # resources_energy
        0,     # resources_diamonds
        500,   # gold_balance (initial)
        1000,  # wood_balance (initial)
        0,     # research_balance (initial)
        
        5000,  # capacity_gold (initial)
        10000, # capacity_wood (initial)
        1000,  # capacity_research (initial)
        
        10,    # gold_rate (initial per hour)
        20,    # wood_rate (initial per hour)
        5,     # research_rate (initial per hour)
        
        1,     # base_level
        1,     # mine_level
        1,     # lumber_house_level
        1,     # warehouse_level
        1,     # barracks_level
        1,     # power_plant_level
        1,     # hospital_level
        1,     # research_lab_level
        1,     # workshop_level
        1,     # jail_level
        0,     # power
        0,     # prestige_level
        0,     # alliance_name
        0,     # alliance_role
        0,     # alliance_joined_at
        0,     # alliance_members_count
        0,     # alliance_power
        "",    # zones_controlled
        0,     # energy
        0,     # energy_max
        0,     # last_daily
        0,     # last_attack
        iso_now, # last_collection (initial)
        0,     # army_infantry
        0,     # army_tank
        0,     # army_artillery
        0,     # army_destroyer
        0,     # army_bm_barrage
        0,     # army_venom_reaper
        0,     # army_titan_crusher
        0,     # items_hazmat_mask
        0,     # items_energy_drink
        0,     # items_repair_kit
        0,     # items_medkit
        0,     # items_radar
        0,     # items_shield_generator
        0,     # items_revive_all
        0,     # items_emp_device
        0,     # items_hazmat_drone
        0,     # timers_base_level
        0,     # timers_mine_level
        0,     # timers_lumber_level
        0,     # timers_warehouse_level
        0,     # timers_barracks_level
        0,     # timers_power_level
        0,     # timers_hospital_level
        0,     # timers_research_level
        0,     # timers_workshop_level
        0,     # timers_jail_level
        "",    # timers_emp_boost_end
        "",    # timers_hazmat_access_end
        0,     # scheduled_zone
        0,     # scheduled_time
        0,     # controlled_zone
    ]
    _players_ws.append_row(new_row)

def get_player_data(user_id: int) -> Dict[str, Any]:
    """Return a dict of all player fields, typed (int or str). Empty if not found."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    row_idx = get_player_row(user_id)
    if row_idx is None:
        return {}
    headers = _players_ws.row_values(1)
    values = _players_ws.row_values(row_idx)
    data: Dict[str, Any] = {}
    for i, h in enumerate(headers):
        val = values[i] if i < len(values) else ""
        print(f"DEBUG: Processing header '{h}', raw value: '{val}'") # Debug print
        if h in [
            "user_id", "resources_wood", "resources_stone", "resources_gold",
            "resources_food", "resources_energy", "resources_diamonds",
            "gold_balance", "wood_balance", "research_balance", # New balance fields
            "capacity_gold", "capacity_wood", "capacity_research", # New capacity fields
            "gold_rate", "wood_rate", "research_rate", # New rate fields
            "base_level", "mine_level", "lumber_house_level", "warehouse_level",
            "barracks_level", "power_plant_level", "hospital_level", "research_lab_level",
            "workshop_level", "jail_level", "power", "prestige_level",
            "alliance_name", "alliance_role", "alliance_joined_at",
            "alliance_members_count", "alliance_power",
            "army_infantry", "army_tank", "army_artillery", "army_destroyer",
            "army_bm_barrage", "army_venom_reaper", "army_titan_crusher",
            "items_hazmat_mask", "items_energy_drink", "items_repair_kit",
            "items_medkit", "items_radar", "items_shield_generator",
            "items_revive_all", "items_emp_device", "items_hazmat_drone", # New item fields
            "timers_base_level", "timers_mine_level", "timers_lumber_level",
            "timers_warehouse_level", "timers_barracks_level", "timers_power_level",
            "timers_hospital_level", "timers_research_level", "timers_workshop_level",
            "timers_jail_level",
            "scheduled_zone", "scheduled_time", "controlled_zone",
            "energy", "energy_max", "last_daily", "last_attack"
        ]:
            try:
                data[h] = int(val)
            except:
                data[h] = 0
        elif h == "zones_controlled":
            data[h] = val.split(",") if val else []
        elif h in ["last_collection", "timers_emp_boost_end", "timers_hazmat_access_end"]:
            # Parse ISO format with timezone. If not present, default to None.
            try:
                data[h] = datetime.fromisoformat(val.rstrip("Z")).replace(tzinfo=timezone.utc) if val else None
            except ValueError:
                data[h] = None # Fallback to None if parsing fails
            print(f"DEBUG: Converted '{h}' to datetime: {data[h]}") # Debug print
        else:
            data[h] = val
            print(f"DEBUG: Converted '{h}' to string: {data[h]}") # Debug print
    print(f"DEBUG: Final player data: {data}") # Debug print
    return data

def update_player_data(user_id: int, field: str, new_value: Any) -> None:
    """Update a specific field for a player."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    try:
        row_idx = get_player_row(user_id)
        if row_idx is None:
            # If user not found, create a new entry with basic data and then update
            # This might create a sparse row if not all new_player data is used
            # Consider a more robust way to create partial data or require full creation
            create_new_player(user_id, "", "New Player") # Placeholder for telegram_username, game_name
            row_idx = get_player_row(user_id) # Re-fetch row index after creation
            if row_idx is None: # Should not happen
                raise ValueError(f"Failed to create or find user ID {user_id} for update.")

        headers = _players_ws.row_values(1)
        if field not in headers:
            # If field doesn't exist, add it to headers and then update
            ensure_headers(_players_ws, [field])
            headers = _players_ws.row_values(1) # Refresh headers after adding new one

        col_idx = headers.index(field) + 1
        # Convert datetime objects to ISO format string before writing to sheet
        if isinstance(new_value, datetime):
            new_value = new_value.isoformat() + "Z"
        _players_ws.update_cell(row_idx, col_idx, new_value)
    except GSpreadException as e:
        raise RuntimeError(f"Failed to update player data: {e}")

def list_all_players() -> List[Dict[str, Any]]:
    """Lists all players in the 'Players' worksheet, returning their data as a list of dictionaries."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    
    headers = _players_ws.row_values(1)
    all_values = _players_ws.get_all_values()
    
    players_data = []
    # Start from the second row to skip headers
    for row_values in all_values[1:]:
        player_data: Dict[str, Any] = {}
        for i, h in enumerate(headers):
            val = row_values[i] if i < len(row_values) else ""
            if h in [
                "user_id", "resources_wood", "resources_stone", "resources_gold",
                "resources_food", "resources_energy", "resources_diamonds",
                "gold_balance", "wood_balance", "research_balance",
                "capacity_gold", "capacity_wood", "capacity_research",
                "gold_rate", "wood_rate", "research_rate",
                "base_level", "mine_level", "lumber_house_level", "warehouse_level",
                "barracks_level", "power_plant_level", "hospital_level", "research_lab_level",
                "workshop_level", "jail_level", "power", "prestige_level",
                "alliance_name", "alliance_role", "alliance_joined_at",
                "alliance_members_count", "alliance_power",
                "army_infantry", "army_tank", "army_artillery", "army_destroyer",
                "army_bm_barrage", "army_venom_reaper", "army_titan_crusher",
                "army_dead_infantry", "army_dead_tanks",
                "items_hazmat_mask", "items_energy_drink", "items_repair_kit",
                "items_medkit", "items_radar", "items_shield_generator",
                "items_revive_all", "items_emp_device", "items_hazmat_drone",
                "items_infinite_scout", "items_speedup_1h", "items_shield_adv",
                "timers_base_level", "timers_mine_level", "timers_lumber_level",
                "timers_warehouse_level", "timers_barracks_level", "timers_power_level",
                "timers_hospital_level", "timers_research_level", "timers_workshop_level",
                "timers_jail_level",
                "scheduled_zone", "scheduled_time", "controlled_zone",
                "energy", "energy_max", "last_daily", "last_attack"
            ]:
                try:
                    player_data[h] = int(val)
                except ValueError:
                    player_data[h] = 0 # Default to 0 if conversion fails
            elif h == "zones_controlled":
                player_data[h] = val.split(",") if val else []
            elif h in ["last_collection", "timers_emp_boost_end", "timers_hazmat_access_end"]:
                try:
                    player_data[h] = datetime.fromisoformat(val.rstrip("Z")).replace(tzinfo=timezone.utc) if val else None
                except ValueError:
                    player_data[h] = None
            else:
                player_data[h] = val
        players_data.append(player_data)
    return players_data

def ensure_headers(ws: gspread.Worksheet, headers: List[str]) -> None:
    """Ensures all specified headers exist in the given worksheet, adding them if missing."""
    existing = ws.row_values(1)
    to_add = [h for h in headers if h not in existing]
    if to_add:
        updated_headers = existing + to_add
        ws.update('A1', [updated_headers])

def _accrue_player_resources_in_sheet(player_id: int) -> None:
    """Accrue resources for a single player by updating their sheet data."""
    player_data = get_player_data(player_id)
    if not player_data:
        print(f"Warning: Player {player_id} not found for resource accrual.")
        return

    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    last_collection_str = player_data.get("last_collection")

    if isinstance(last_collection_str, str):
        try:
            last_collection = datetime.fromisoformat(last_collection_str.rstrip("Z")).replace(tzinfo=timezone.utc)
        except ValueError:
            last_collection = now_utc # Default if parsing fails
    elif isinstance(last_collection_str, datetime):
        last_collection = last_collection_str
    else:
        last_collection = now_utc

    time_since_last_collection = (now_utc - last_collection).total_seconds()
    if time_since_last_collection < 0: # Handle potential clock skew or future time
        time_since_last_collection = 0

    # Production rates are per hour, convert to per second
    wood_rate_per_sec = player_data.get("wood_rate", 0) / 3600.0
    stone_rate_per_sec = player_data.get("stone_rate", 0) / 3600.0
    food_rate_per_sec = player_data.get("food_rate", 0) / 3600.0
    gold_rate_per_sec = player_data.get("gold_rate", 0) / 3600.0
    research_rate_per_sec = player_data.get("research_rate", 0) / 3600.0
    energy_rate_per_sec = player_data.get("energy_rate", 0) / 3600.0

    # Current resources and capacities
    current_wood = player_data.get("resources_wood", 0)
    current_stone = player_data.get("resources_stone", 0)
    current_food = player_data.get("resources_food", 0)
    current_gold = player_data.get("resources_gold", 0)
    current_research = player_data.get("research_balance", 0)
    current_energy = player_data.get("resources_energy", 0)

    wood_capacity = player_data.get("capacity_wood", 10000) # Default capacity
    stone_capacity = player_data.get("capacity_stone", 10000) # Assuming stone also has capacity
    food_capacity = player_data.get("capacity_food", 10000) # Assuming food also has capacity
    gold_capacity = player_data.get("capacity_gold", 5000) # Default capacity
    research_capacity = player_data.get("capacity_research", 1000) # Default capacity
    energy_capacity = player_data.get("energy_max", 2000) # Assuming energy has capacity

    # Calculate accrued resources, capped by capacity
    accrued_wood = min(current_wood + (wood_rate_per_sec * time_since_last_collection), wood_capacity)
    accrued_stone = min(current_stone + (stone_rate_per_sec * time_since_last_collection), stone_capacity)
    accrued_food = min(current_food + (food_rate_per_sec * time_since_last_collection), food_capacity)
    accrued_gold = min(current_gold + (gold_rate_per_sec * time_since_last_collection), gold_capacity)
    accrued_research = min(current_research + (research_rate_per_sec * time_since_last_collection), research_capacity)
    accrued_energy = min(current_energy + (energy_rate_per_sec * time_since_last_collection), energy_capacity)

    # Update sheet
    update_player_data(player_id, "resources_wood", int(accrued_wood))
    update_player_data(player_id, "resources_stone", int(accrued_stone))
    update_player_data(player_id, "resources_food", int(accrued_food))
    update_player_data(player_id, "resources_gold", int(accrued_gold))
    update_player_data(player_id, "research_balance", int(accrued_research))
    update_player_data(player_id, "resources_energy", int(accrued_energy))
    update_player_data(player_id, "last_collection", now_utc.isoformat() + "Z")

def accrue(balance_key, rate_per_sec, cap_key):
    # This function seems to be unused or a placeholder. 
    # The logic is handled directly in _accrue_player_resources_in_sheet.
    pass # No operation, function will be removed or commented out. 

def get_pending_upgrades() -> List[Dict[str, Any]]:
    """Fetches all pending upgrades from the sheet."""
    try:
        sheet = get_sheet("pending_upgrades")
        if not sheet:
            return []
        
        # Get all rows except header
        rows = sheet.get_all_records()
        upgrades = []
        
        for row in rows:
            try:
                upgrades.append({
                    "id": row["id"],
                    "user_id": int(row["user_id"]),
                    "building_key": row["building_key"],
                    "new_level": int(row["new_level"]),
                    "finish_at": datetime.fromisoformat(row["finish_at"].replace("Z", "+00:00"))
                })
            except (ValueError, KeyError):
                continue
        
        return upgrades
    except Exception as e:
        print(f"Error fetching pending upgrades: {e}")
        return []

def add_pending_upgrade(user_id: int, building_key: str, new_level: int, finish_at: datetime) -> bool:
    """Adds a new pending upgrade to the sheet."""
    try:
        sheet = get_sheet("pending_upgrades")
        if not sheet:
            return False
        
        # Get next ID
        rows = sheet.get_all_records()
        next_id = max([int(row["id"]) for row in rows], default=0) + 1
        
        # Add new row
        sheet.append_row([
            str(next_id),
            str(user_id),
            building_key,
            str(new_level),
            finish_at.isoformat() + "Z"
        ])
        return True
    except Exception as e:
        print(f"Error adding pending upgrade: {e}")
        return False

def remove_pending_upgrade(upgrade_id: int) -> bool:
    """Removes a pending upgrade from the sheet."""
    try:
        sheet = get_sheet("pending_upgrades")
        if not sheet:
            return False
        
        # Find row with matching ID
        rows = sheet.get_all_records()
        for i, row in enumerate(rows, start=2):  # start=2 because sheet is 1-indexed and has header
            if int(row["id"]) == upgrade_id:
                sheet.delete_row(i)
                return True
        return False
    except Exception as e:
        print(f"Error removing pending upgrade: {e}")
        return False

def get_due_upgrades(now: datetime) -> List[Dict[str, Any]]:
    """Fetches all upgrades that are due to complete."""
    upgrades = get_pending_upgrades()
    return [u for u in upgrades if u["finish_at"] <= now]

def apply_building_level(user_id: int, building_key: str, new_level: int) -> bool:
    """Applies a building level upgrade to the player's data."""
    try:
        field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
        if not field_name:
            return False
        
        # Update the building level
        update_player_data(user_id, field_name, new_level)
        
        # Recalculate and update player stats
        data = get_player_data(user_id)
        if data:
            updated_data = apply_building_effects(data)
            for key, value in updated_data.items():
                if key.startswith("resources_") or key.endswith("_level"):
                    update_player_data(user_id, key, value)
        
        return True
    except Exception as e:
        print(f"Error applying building level: {e}")
        return False

def get_player_buildings(user_id: int) -> Dict[str, int]:
    """
    Fetch just the current building levels for user_id,
    returning a mapping from building_key to its integer level.
    """
    player = get_player_data(user_id)
    if not player:
        return {}
        
    return {
        'lumber_house': int(player.get('lumber_house_level', 0)),
        'mine':         int(player.get('mine_level', 0)),
        'warehouse':    int(player.get('warehouse_level', 0)),
        'hospital':     int(player.get('hospital_level', 0)),
        'research_lab': int(player.get('research_lab_level', 0)),
        'barracks':     int(player.get('barracks_level', 0)),
        'power_plant':  int(player.get('power_plant_level', 0)),
        'workshop':     int(player.get('workshop_level', 0)),
        'jail':         int(player.get('jail_level', 0)),
    }

# Cursor Prompt (for future regeneration):
# "Generate a file modules/sheets_helper.py that decodes BASE64_CREDS,
#  authenticates to Google Sheets via google-auth and gspread, ensures
#  a 'Players' worksheet with the specified headers exists, and exposes
#  helper functions: initialize_sheets(), get_player_row(), create_new_player(),
#  get_player_data(), update_player_data(), list_all_players(). Use ISO timestamps,
#  Python types for sheet values, and handle missing-column or missing-sheet cases gracefully." 