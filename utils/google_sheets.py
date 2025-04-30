import os
import json
import base64
from datetime import datetime
import gspread
from gspread.exceptions import WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials

# === Environment-driven Google Sheets Setup ===

# Sheet ID from environment
SHEET_ID = os.environ.get("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("Missing SHEET_ID env var")

# Base64-encoded service account JSON
creds_b64 = os.environ.get("GOOGLE_CREDS_BASE64")
if not creds_b64:
    raise RuntimeError("Missing GOOGLE_CREDS_BASE64 env var")

# Decode and load credentials
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
    "army": ["player_id", "unit_name", "amount"],
    "training": ["task_id", "player_id", "unit_name", "amount", "end_time"],
    "battle_history": [
        "player_id", "target_id", "outcome", "rewards", "date", "battle_log",
    ],
    "missions": ["player_id", "date", "missions"],
    "resources": ["player_id", "metal", "fuel", "crystal", "credits"],
    "buildings": ["player_id", "building_name", "level"],
    "purchases": ["player_id", "item_id", "date"],
    "building_queue": ["task_id", "player_id", "building_name", "end_time"],
}

# === Worksheet Loading ===

def _get_worksheet(name: str):
    """Gets a worksheet by name, creating it if necessary."""
    try:
        return sheet.worksheet(WORKSHEETS[name])
    except WorksheetNotFound:
        new_ws = sheet.add_worksheet(
            title=WORKSHEETS[name], rows=100, cols=10
        )
        new_ws.append_row(HEADERS[name])
        return new_ws

# Initialize worksheets
army_ws = _get_worksheet("army")
training_ws = _get_worksheet("training")
battle_ws = _get_worksheet("battle_history")
missions_ws = _get_worksheet("missions")
resources_ws = _get_worksheet("resources")
buildings_ws = _get_worksheet("buildings")
purchases_ws = _get_worksheet("purchases")
building_queue_ws = _get_worksheet("building_queue")

# === Army Sheet Functions ===

def load_player_army(player_id: str) -> dict:
    """Loads the player's army from the sheet."""
    try:
        recs = army_ws.get_all_records()
        army = {}
        for row in recs:
            if str(row.get("player_id")) == str(player_id):
                army[row["unit_name"]] = row["amount"]
        return army
    except Exception as e:
        print("load_player_army error:", e)
        return {}


def save_player_army(player_id: str, army: dict) -> None:
    """Saves the player's army, overwriting existing entries."""
    try:
        # Clear existing
        for cell in army_ws.findall(str(player_id)):
            army_ws.delete_row(cell.row)
        # Save current
        rows = [[player_id, unit, qty] for unit, qty in army.items()]
        army_ws.append_rows(rows)
    except Exception as e:
        print("save_player_army error:", e)

# === Training Queue Functions ===

def load_training_queue(player_id: str) -> dict:
    """Loads the player's training queue."""
    try:
        recs = training_ws.get_all_records()
        return {row["task_id"]: row for row in recs if str(row.get("player_id")) == str(player_id)}
    except Exception as e:
        print("load_training_queue error:", e)
        return {}


def save_training_task(player_id: str, unit_name: str, amount: int, end_time: str) -> None:
    """Saves a training task."""
    try:
        task_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        training_ws.append_row([task_id, player_id, unit_name, amount, end_time])
    except Exception as e:
        print("save_training_task error:", e)


def delete_training_task(task_id: str) -> None:
    """Deletes a training task by ID."""
    try:
        for cell in training_ws.findall(str(task_id)):
            training_ws.delete_row(cell.row)
    except Exception as e:
        print("delete_training_task error:", e)

# === Battle History Functions ===

def save_battle_result(player_id: str, target_id: str, outcome: str, rewards: str, date: str, battle_log: str) -> None:
    """Saves a battle result."""
    try:
        battle_ws.append_row([player_id, target_id, outcome, rewards, date, battle_log])
    except Exception as e:
        print("save_battle_result error:", e)


def load_battle_history(player_id: str) -> list:
    """Loads the player's battle history."""
    try:
        recs = battle_ws.get_all_records()
        return [row for row in recs if str(row.get("player_id")) == str(player_id)]
    except Exception as e:
        print("load_battle_history error:", e)
        return []

# === Missions Functions ===

def load_player_missions(player_id: str) -> dict | None:
    """Loads the player's missions data (if any)."""
    try:
        recs = missions_ws.get_all_records()
        for row in recs:
            if str(row.get("player_id")) == str(player_id):
                return json.loads(row.get("missions", "{}").replace("'", '"'))
        return None
    except Exception as e:
        print("load_player_missions error:", e)
        return None


def save_player_missions(player_id: str, missions: dict) -> None:
    """Saves the player's missions data, overwriting existing."""
    try:
        # Clear existing
        for cell in missions_ws.findall(str(player_id)):
            missions_ws.delete_row(cell.row)
        # Save current
        missions_ws.append_row([
            player_id,
            str(datetime.now().date()),
            json.dumps(missions),
        ])
    except Exception as e:
        print("save_player_missions error:", e)

# === Resources Functions ===

def load_resources(player_id: str) -> dict:
    """Loads the player's resources."""
    try:
        recs = resources_ws.get_all_records()
        for row in recs:
            if str(row.get("player_id")) == str(player_id):
                return {
                    "metal": row.get("metal", 0),
                    "fuel": row.get("fuel", 0),
                    "crystal": row.get("crystal", 0),
                    "credits": row.get("credits", 0),
                }
        return {"metal": 0, "fuel": 0, "crystal": 0, "credits": 0}
    except Exception as e:
        print("load_resources error:", e)
        return {"metal": 0, "fuel": 0, "crystal": 0, "credits": 0}


def save_resources(player_id: str, resources: dict) -> None:
    """Saves the player's resources, overwriting existing."""
    try:
        # Clear existing
        for cell in resources_ws.findall(str(player_id)):
            resources_ws.delete_row(cell.row)
        # Save current
        resources_ws.append_row([
            player_id,
            resources.get("metal", 0),
            resources.get("fuel", 0),
            resources.get("crystal", 0),
            resources.get("credits", 0),
        ])
    except Exception as e:
        print("save_resources error:", e)

# === Building Queue Functions ===

def load_building_queue(player_id: str) -> dict:
    """Loads the building queue for a player."""
    try:
        recs = building_queue_ws.get_all_records()
        return {row["task_id"]: row for row in recs if str(row.get("player_id")) == str(player_id)}
    except Exception as e:
        print("load_building_queue error:", e)
        return {}


def save_building_task(player_id: str, building_name: str, end_time: str) -> None:
    """Saves a building task to the queue."""
    try:
        task_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        building_queue_ws.append_row([task_id, player_id, building_name, end_time])
    except Exception as e:
        print("save_building_task error:", e)


def delete_building_task(task_id: str) -> None:
    """Deletes a building task by ID."""
    try:
        for cell in building_queue_ws.findall(str(task_id)):
            building_queue_ws.delete_row(cell.row)
    except Exception as e:
        print("delete_building_task error:", e)

# === Building Level Helpers ===

def save_building_level(player_id: str, building_name: str, new_level: int) -> None:
    """Updates the player's building level."""
    try:
        for cell in buildings_ws.findall(str(player_id)):
            if buildings_ws.cell(cell.row, 2).value == building_name:
                buildings_ws.delete_row(cell.row)
        buildings_ws.append_row([player_id, building_name, new_level])
    except Exception as e:
        print("save_building_level error:", e)


def get_building_level(player_id: str, building_name: str) -> int:
    """Retrieves the player's building level."""
    try:
        recs = buildings_ws.get_all_records()
        for row in recs:
            if str(row.get("player_id")) == str(player_id) and row.get("building_name") == building_name:
                return int(row.get("level", 0))
        return 0
    except Exception as e:
        print("get_building_level error:", e)
        return 0

# === Miscellaneous Queries ===

def get_training_total(player_id: str, unit: str) -> int:
    """Returns total trained units of a type."""
    try:
        return load_player_army(player_id).get(unit, 0)
    except:
        return 0


def get_mined_total(player_id: str, resource: str) -> int:
    """Returns total mined resources of a type."""
    try:
        return load_resources(player_id).get(resource, 0)
    except:
        return 0


def get_attack_count(player_id: str) -> int:
    """Returns total attack count."""
    try:
        recs = battle_ws.get_all_records()
        return sum(1 for r in recs if str(r.get("player_id")) == str(player_id))
    except:
        return 0
