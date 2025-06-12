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
    
    # Black Market Items
    "items_hazmat_mask", "items_energy_drink", "items_repair_kit",
    "items_medkit", "items_radar", "items_shield_generator",
    "items_revive_all", "items_emp_device", "items_hazmat_drone", # New item fields
    
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
    iso_now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
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
        else:
            data[h] = val
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
    """Return a list of all players as dicts of header→value."""
    if _players_ws is None:
        raise RuntimeError("Sheets not initialized. Call initialize_sheets() first.")
    all_vals = _players_ws.get_all_values()
    headers = all_vals[0]
    players: List[Dict[str, Any]] = []
    for row in all_vals[1:]:
        entry = {}
        for i, h in enumerate(headers):
            entry[h] = row[i] if i < len(row) else ""
        players.append(entry)
    return players

def ensure_headers(ws: gspread.Worksheet, headers: List[str]) -> None:
    """Ensure all needed headers exist in the first row."""
    try:
        existing_headers = ws.row_values(1)
        next_col = len(existing_headers) + 1
        
        for header in headers:
            if header not in existing_headers:
                ws.update_cell(1, next_col, header)
                next_col += 1
    except GSpreadException as e:
        raise RuntimeError(f"Failed to ensure headers: {e}")

def tick_resources(player_id: int) -> None:
    """
    Calculate time-based resource gains since last_collection,
    cap by capacity, update balances and last_collection timestamp.
    """
    # 1. Fetch raw player data from sheet
    data = get_player_data(player_id)
    last_ts = data.get("last_collection")
    if not last_ts:
        # If no timestamp, just set it now and exit
        now = datetime.now(timezone.utc)
        update_player_data(player_id, "last_collection", now.isoformat() + "Z")
        return

    # 2. Parse timestamps
    # strip trailing 'Z' if present, then parse as UTC
    try:
        # Ensure last_ts is a string before rstrip and fromisoformat
        if isinstance(last_ts, datetime):
            last = last_ts # Already a datetime object if from get_player_data
        else:
            last = datetime.fromisoformat(str(last_ts).rstrip("Z")).replace(tzinfo=timezone.utc)
    except Exception:
        last = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds()

    # 3. Compute per-second rates (stored in sheet as per-hour)
    #    (if your sheet stores per-hour, divide by 3600; otherwise they may already be per-sec)
    gold_rate_per_sec     = data.get("gold_rate", 0)     / 3600
    wood_rate_per_sec     = data.get("wood_rate", 0)     / 3600
    research_rate_per_sec = data.get("research_rate", 0) / 3600

    # 4. Calculate gains and cap by capacity
    def accrue(balance_key, rate_per_sec, cap_key):
        bal = data.get(balance_key, 0)
        cap = data.get(cap_key, 0)
        gain = rate_per_sec * elapsed
        new_bal = min(bal + gain, cap)
        return new_bal

    new_gold     = accrue("gold_balance",     gold_rate_per_sec,     "capacity_gold")
    new_wood     = accrue("wood_balance",     wood_rate_per_sec,     "capacity_wood")
    new_research = accrue("research_balance", research_rate_per_sec, "capacity_research")

    # 5. Write back updated balances + timestamp
    update_player_data(player_id, "gold_balance",     round(new_gold))
    update_player_data(player_id, "wood_balance",     round(new_wood))
    update_player_data(player_id, "research_balance", round(new_research))
    update_player_data(player_id, "last_collection",  now.isoformat() + "Z")

# Cursor Prompt (for future regeneration):
# "Generate a file modules/sheets_helper.py that decodes BASE64_CREDS,
#  authenticates to Google Sheets via google-auth and gspread, ensures
#  a 'Players' worksheet with the specified headers exists, and exposes
#  helper functions: initialize_sheets(), get_player_row(), create_new_player(),
#  get_player_data(), update_player_data(), list_all_players(). Use ISO timestamps,
#  Python types for sheet values, and handle missing-column or missing-sheet cases gracefully." 