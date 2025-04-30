import os
import json
import base64
import logging
from datetime import datetime

import gspread
from gspread.exceptions import WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)

# === Environment-driven Google Sheets Setup ===

SHEET_ID = os.environ.get("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("Missing SHEET_ID env var")

creds_b64 = os.environ.get("GOOGLE_CREDS_BASE64")
if not creds_b64:
    raise RuntimeError("Missing GOOGLE_CREDS_BASE64 env var")

creds_info = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# === Worksheet Names & Headers ===
WORKSHEETS = {
    "army": "army",
    "training": "training",
    "battle_history": "battle_history",
    "missions": "player_missions",
    "resources": "resources",
    "buildings": "buildings",
    "purchases": "purchases",
    "building_queue": "building_queue",
}

HEADERS = {
    "army": ["player_id", "unit", "quantity", "level", "attack", "defense", "hp", "speed"],
    "training": ["task_id", "player_id", "unit_name", "amount", "end_time", "type", "upgrade_level"],
    "battle_history": [
        "battle_id", "player_id", "target_id", "tactic", "outcome", "rewards", "timestamp"
    ],
    "missions": ["player_id", "mission_id", "completed"],
    "resources": ["player_id", "metal", "fuel", "crystal", "credits"],
    "buildings": ["player_id", "building_name", "level"],
    "purchases": ["player_id", "item_id", "amount", "timestamp"],
    "building_queue": ["task_id", "player_id", "building_name", "end_time"],
}


def get_worksheet(name: str):
    """
    Retrieves (or creates) a worksheet and ensures correct headers.
    """
    title = WORKSHEETS[name]
    headers = HEADERS[name]
    try:
        ws = sheet.worksheet(title)
    except WorksheetNotFound:
        logger.info(f"Worksheet '{title}' not found. Creating.")
        ws = sheet.add_worksheet(title=title, rows=1000, cols=len(headers))
    # Ensure header row
    first_row = ws.row_values(1)
    if first_row != headers:
        logger.info(f"Updating headers for worksheet '{title}'.")
        ws.update('A1', [headers])
    return ws

# Instantiate worksheets
army_ws = get_worksheet("army")
training_ws = get_worksheet("training")
battle_history_ws = get_worksheet("battle_history")
missions_ws = get_worksheet("missions")
resources_ws = get_worksheet("resources")
buildings_ws = get_worksheet("buildings")
purchases_ws = get_worksheet("purchases")
building_queue_ws = get_worksheet("building_queue")

# === Army Sheet Functions ===

def load_player_army(player_id: str) -> dict:
    """Loads player's army composition with stats and levels."""
    try:
        recs = army_ws.get_all_records()
        army = {}
        for row in recs:
            if str(row.get("player_id")) == str(player_id):
                unit = row.get("unit")
                qty = row.get("quantity", 0)
                army[unit] = qty
                for attr in ("level", "attack", "defense", "hp", "speed"):
                    val = row.get(attr)
                    if val:
                        army[f"{unit}_{attr}"] = val
        return army
    except Exception as e:
        logger.exception("Error loading player army:")
        return {}


def save_player_army(player_id: str, army: dict):
    """Saves player's army composition with stats and levels."""
    try:
        # Remove existing rows for player
        for cell in army_ws.findall(str(player_id)):
            army_ws.delete_row(cell.row)
        # Append new rows
        for unit, qty in army.items():
            if unit.endswith("_level") or "_attack" in unit or "_defense" in unit or "_hp" in unit or "_speed" in unit:
                continue
            level = army.get(f"{unit}_level", 0)
            atk = army.get(f"{unit}_attack", 0)
            df = army.get(f"{unit}_defense", 0)
            hp = army.get(f"{unit}_hp", 0)
            spd = army.get(f"{unit}_speed", 0)
            army_ws.append_row([player_id, unit, qty, level, atk, df, hp, spd])
    except Exception as e:
        logger.exception("Error saving player army:")

# === Training Queue Functions ===

def load_training_queue(player_id: str) -> dict:
    """Loads the player's training/upgrades queue."""
    try:
        recs = training_ws.get_all_records()
        queue = {}
        for row in recs:
            if str(row.get("player_id")) == str(player_id):
                tid = row.get("task_id")
                queue[tid] = {
                    "unit_name": row.get("unit_name"),
                    "amount": row.get("amount", 0),
                    "end_time": row.get("end_time"),
                    "type": row.get("type"),
                    "upgrade_level": row.get("upgrade_level", 0),
                }
        return queue
    except Exception as e:
        logger.exception("Error loading training queue:")
        return {}


def save_training_task(player_id: str, unit_name: str, amount, end_time: str, task_type="train", upgrade_level=0):
    """Saves a training or upgrade task."""
    try:
        task_id = f"{player_id}-{int(datetime.now().timestamp()*1000)}"
        training_ws.append_row([
            task_id,
            player_id,
            unit_name,
            amount,
            end_time,
            task_type,
            upgrade_level,
        ])
    except Exception as e:
        logger.exception("Error saving training task:")


def delete_training_task(task_id: str):
    """Deletes a training or upgrade task by its ID."""
    try:
        for cell in training_ws.findall(task_id):
            training_ws.delete_row(cell.row)
    except Exception as e:
        logger.exception("Error deleting training task:")

# === Battle History Functions ===

def save_battle_result(battle_id: str, player_id: str, target_id: str, tactic: str,
                       outcome: str, rewards: str, timestamp: str):
    """Appends a new battle result record."""
    try:
        battle_history_ws.append_row([
            battle_id, player_id, target_id, tactic, outcome, rewards, timestamp
        ])
    except Exception as e:
        logger.exception("Error saving battle result:")


def load_battle_history(player_id: str) -> list:
    """Loads all past battles for a player."""
    try:
        recs = battle_history_ws.get_all_records()
        return [r for r in recs if str(r.get("player_id")) == str(player_id)]
    except Exception as e:
        logger.exception("Error loading battle history:")
        return []

# === Missions Functions ===
def load_player_missions(player_id: str) -> list:
    """Loads a player's mission states."""
    try:
        recs = missions_ws.get_all_records()
        return [r for r in recs if str(r.get("player_id")) == str(player_id)]
    except Exception as e:
        logger.exception("Error loading missions:")
        return []


def save_player_mission(player_id: str, mission_id: str, completed: bool):
    """Saves or updates a player's mission state."""
    try:
        # delete existing
        for cell in missions_ws.findall(f"^{player_id}$", in_column=1):
            if missions_ws.cell(cell.row, 2).value == mission_id:
                missions_ws.delete_row(cell.row)
        missions_ws.append_row([player_id, mission_id, completed])
    except Exception as e:
        logger.exception("Error saving mission:")

# === Resource Functions ===

def load_resources(player_id: str) -> dict:
    """Loads the player's resources, defaults to zero if missing."""
    try:
        recs = resources_ws.get_all_records()
        for row in recs:
            if str(row.get("player_id")) == str(player_id):
                return {k: row.get(k, 0) for k in HEADERS["resources"][1:]}
        return {k: 0 for k in HEADERS["resources"][1:]}
    except Exception as e:
        logger.exception("Error loading resources:")
        return {k: 0 for k in HEADERS["resources"][1:]}


def save_resources(player_id: str, resources: dict):
    """Saves the player's resources."""
    try:
        for cell in resources_ws.findall(str(player_id)):
            resources_ws.delete_row(cell.row)
        resources_ws.append_row([
            player_id,
            resources.get("metal", 0),
            resources.get("fuel", 0),
            resources.get("crystal", 0),
            resources.get("credits", 0),
        ])
    except Exception as e:
        logger.exception("Error saving resources:")

# === Building Level Helpers ===

def load_building_queue(player_id: str) -> dict:
    """Returns active building tasks."""
    try:
        recs = building_queue_ws.get_all_records()
        return {r.get("task_id"): r for r in recs if str(r.get("player_id")) == str(player_id)}
    except Exception as e:
        logger.exception("Error loading building queue:")
        return {}


def save_building_task(player_id: str, building_name: str, end_time: str):
    """Schedules a new building upgrade task."""
    try:
        task_id = f"{player_id}-{int(datetime.now().timestamp()*1000)}"
        building_queue_ws.append_row([task_id, player_id, building_name, end_time])
    except Exception as e:
        logger.exception("Error saving building task:")


def delete_building_task(task_id: str):
    """Deletes a building task by its ID."""
    try:
        for cell in building_queue_ws.findall(task_id):
            building_queue_ws.delete_row(cell.row)
    except Exception as e:
        logger.exception("Error deleting building task:")


def save_building_level(player_id: str, building_name: str, new_level: int):
    """Updates a building's level record."""
    try:
        for cell in buildings_ws.findall(str(player_id)):
            if buildings_ws.cell(cell.row, 2).value == building_name:
                buildings_ws.delete_row(cell.row)
        buildings_ws.append_row([player_id, building_name, new_level])
    except Exception as e:
        logger.exception("Error saving building level:")


def get_building_level(player_id: str, building_name: str) -> int:
    """Retrieves a building's current level."""
    try:
        recs = buildings_ws.get_all_records()
        for row in recs:
            if str(row.get("player_id")) == str(player_id) and row.get("building_name") == building_name:
                return int(row.get("level", 0))
        return 0
    except Exception as e:
        logger.exception("Error getting building level:")
        return 0

# === Miscellaneous Queries ===
def get_training_total(player_id: str, unit: str) -> int:
    try:
        return load_player_army(player_id).get(unit, 0)
    except Exception:
        return 0

def get_mined_total(player_id: str, resource: str) -> int:
    try:
        return load_resources(player_id).get(resource, 0)
    except Exception:
        return 0
