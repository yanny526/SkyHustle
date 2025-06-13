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
    try:
        cell = _players_ws.find(str(user_id), in_column=1)
        return cell.row
    except GSpreadException:
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
        0,     # resources_energy
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
        for i, header in enumerate(headers):
            val = row_values[i] if i < len(row_values) else ""
            player_data[header] = val # Store as string, convert when reading specific fields
        players_data.append(player_data)
    return players_data

def ensure_headers(ws: gspread.Worksheet, headers: List[str]) -> None:
    """Ensure a worksheet has all required headers, adding missing ones."""
    existing_headers = ws.row_values(1)
    missing_headers = [h for h in headers if h not in existing_headers]
    if missing_headers:
        ws.append_row(missing_headers)

def _accrue_player_resources_in_sheet(player_id: int) -> None:
    """Accrue resources for a player based on their production rates and last collection time.
    This function is intended for internal use by the resource ticking mechanism.
    """
    player_data = get_player_data(player_id)
    if not player_data:
        print(f"Player {player_id} not found for resource accrual.")
        return

    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)

    # Get last collection time
    last_collection_str = player_data.get("last_collection")
    if last_collection_str and isinstance(last_collection_str, str):
        try:
            last_collection_dt = datetime.fromisoformat(last_collection_str.replace("Z", "")).replace(tzinfo=timezone.utc)
        except ValueError:
            last_collection_dt = now_utc  # Fallback if format is bad
    else:
        last_collection_dt = now_utc

    # Calculate elapsed time in seconds
    elapsed_seconds = (now_utc - last_collection_dt).total_seconds()

    if elapsed_seconds <= 0:
        # No time has passed, or time went backwards (shouldn't happen)
        return

    # Get current resources and production rates (per hour)
    wood = int(player_data.get("resources_wood", 0))
    stone = int(player_data.get("resources_stone", 0))
    food = int(player_data.get("resources_food", 0))
    gold = int(player_data.get("resources_gold", 0))
    energy = int(player_data.get("resources_energy", 0))

    # Get building levels to determine rates
    lumber_lvl = int(player_data.get("lumber_house_level", 1))
    mine_lvl = int(player_data.get("mine_level", 1))
    warehouse_lvl = int(player_data.get("warehouse_level", 1))
    powerplant_lvl = int(player_data.get("power_plant_level", 1))
    base_lvl = int(player_data.get("base_level", 1))

    # Production rates per hour based on levels (simplified for now)
    wood_per_hour = lumber_lvl * 60.0 # Example: 60 wood per hour per level
    stone_per_hour = mine_lvl * 50.0  # Example: 50 stone per hour per level
    food_per_hour = warehouse_lvl * 40.0 # Example: 40 food per hour per level
    gold_per_hour = mine_lvl * 30.0  # Example: 30 gold per hour per level
    energy_per_hour = powerplant_lvl * 20.0 # Example: 20 energy per hour per level
    energy_max = base_lvl * 200 # Example: Max energy tied to base level

    # Calculate accrued resources
    wood_delta = (wood_per_hour / 3600) * elapsed_seconds
    stone_delta = (stone_per_hour / 3600) * elapsed_seconds
    food_delta = (food_per_hour / 3600) * elapsed_seconds
    gold_delta = (gold_per_hour / 3600) * elapsed_seconds
    energy_delta = (energy_per_hour / 3600) * elapsed_seconds

    # Add to current balance (only integer part)
    wood += int(wood_delta)
    stone += int(stone_delta)
    food += int(food_delta)
    gold += int(gold_delta)
    energy = min(energy + int(energy_delta), energy_max) # Cap energy at max

    # Update player data in Sheets
    updates = {
        "resources_wood": wood,
        "resources_stone": stone,
        "resources_food": food,
        "resources_gold": gold,
        "resources_energy": energy,
        "last_collection": now_utc.isoformat() + "Z" # Update last tick time
    }
    
    for field, value in updates.items():
        update_player_data(player_id, field, value)

def accrue(balance_key, rate_per_sec, cap_key):
    """This function is now obsolete and will be removed."""
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

# Cursor Prompt (for future regeneration):
# "Generate a file modules/sheets_helper.py that decodes BASE64_CREDS,
#  authenticates to Google Sheets via google-auth and gspread, ensures
#  a 'Players' worksheet with the specified headers exists, and exposes
#  helper functions: initialize_sheets(), get_player_row(), create_new_player(),
#  get_player_data(), update_player_data(), list_all_players(). Use ISO timestamps,
#  Python types for sheet values, and handle missing-column or missing-sheet cases gracefully." 