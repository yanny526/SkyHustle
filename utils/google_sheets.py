# google_sheets.py (Part 1 of X – Render-Compatible)

import os
import json
import base64
import gspread
from google.oauth2.service_account import Credentials

# ── Decode base64 Google creds from env ──────────────────────────────────
creds_base64 = os.environ.get("GOOGLE_CREDS_BASE64")
sheet_id = os.environ.get("SHEET_ID")

decoded_bytes = base64.b64decode(creds_base64)
creds_dict = json.loads(decoded_bytes)

# ── Authenticate Sheets API ──────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open_by_key(sheet_id)

# ── Sheet Tabs ───────────────────────────────────────────────────────────
PLAYER_SHEET = SHEET.worksheet("players")
MISSION_SHEET = SHEET.worksheet("missions")
BUILDING_SHEET = SHEET.worksheet("buildings")
ARMY_SHEET = SHEET.worksheet("army")
SPY_SHEET = SHEET.worksheet("spy_logs")
BLACKMARKET_SHEET = SHEET.worksheet("blackmarket_logs")
REWARDS_SHEET = SHEET.worksheet("rewards")
TECH_SHEET = SHEET.worksheet("tech_tree")
ZONE_SHEET = SHEET.worksheet("zones")
STORE_SHEET = SHEET.worksheet("store_logs")

# ── Player Row Lookup ────────────────────────────────────────────────────
def get_player_row(user_id: int):
    data = PLAYER_SHEET.col_values(1)
    if str(user_id) in data:
        return data.index(str(user_id)) + 1
    else:
        PLAYER_SHEET.append_row([str(user_id), 0, 0, 0, 0])  # user_id, metal, energy, oil, credits
        return len(data) + 1
# google_sheets.py (Part 2 of X)

def load_player_data(user_id: int):
    row = get_player_row(user_id)
    values = PLAYER_SHEET.row_values(row)
    return {
        "user_id": values[0],
        "metal": int(values[1]),
        "energy": int(values[2]),
        "oil": int(values[3]),
        "credits": int(values[4]),
    }

def save_player_data(user_id: int, metal: int, energy: int, oil: int, credits: int):
    row = get_player_row(user_id)
    PLAYER_SHEET.update(f"B{row}:E{row}", [[metal, energy, oil, credits]])

def load_buildings(user_id: int):
    data = BUILDING_SHEET.get_all_records()
    return {row['building']: row['level'] for row in data if str(row['user_id']) == str(user_id)}

def save_building_level(user_id: int, building: str, level: int):
    all_data = BUILDING_SHEET.get_all_records()
    for i, row in enumerate(all_data):
        if str(row['user_id']) == str(user_id) and row['building'] == building:
            BUILDING_SHEET.update_cell(i+2, 3, level)
            return
    BUILDING_SHEET.append_row([str(user_id), building, level])
# google_sheets.py (Part 3 of X)

def load_army(user_id: int):
    data = ARMY_SHEET.get_all_records()
    return {row["unit"]: row["count"] for row in data if str(row["user_id"]) == str(user_id)}

def save_army_unit(user_id: int, unit: str, count: int):
    data = ARMY_SHEET.get_all_records()
    for i, row in enumerate(data):
        if str(row["user_id"]) == str(user_id) and row["unit"] == unit:
            ARMY_SHEET.update_cell(i+2, 3, count)
            return
    ARMY_SHEET.append_row([str(user_id), unit, count])

def load_tech_tree(user_id: int):
    data = TECH_SHEET.get_all_records()
    return {row["tech"]: row["level"] for row in data if str(row["user_id"]) == str(user_id)}

def save_tech_progress(user_id: int, tech: str, level: int):
    data = TECH_SHEET.get_all_records()
    for i, row in enumerate(data):
        if str(row["user_id"]) == str(user_id) and row["tech"] == tech:
            TECH_SHEET.update_cell(i+2, 3, level)
            return
    TECH_SHEET.append_row([str(user_id), tech, level])

def log_mission_completion(user_id: int, mission_name: str):
    MISSION_SHEET.append_row([str(user_id), mission_name])

def has_completed_mission(user_id: int, mission_name: str):
    data = MISSION_SHEET.get_all_values()
    return [str(user_id), mission_name] in data
# google_sheets.py (Part 4 of X)

from datetime import datetime

def log_reward_claim(user_id: int, reward_type: str):
    REWARDS_SHEET.append_row([str(user_id), reward_type, datetime.utcnow().isoformat()])

def has_claimed_reward(user_id: int, reward_type: str):
    data = REWARDS_SHEET.get_all_records()
    return any(
        str(row["user_id"]) == str(user_id) and row["reward_type"] == reward_type
        for row in data
    )

def save_blackmarket_purchase(user_id: int, item_key: str):
    BLACKMARKET_SHEET.append_row([str(user_id), item_key, datetime.utcnow().isoformat()])

def log_spy_activity(scout_id: int, target_id: int, result: str):
    SPY_SHEET.append_row([
        str(scout_id), str(target_id), result, datetime.utcnow().isoformat()
    ])

def save_store_purchase(user_id: int, item_name: str, credits_spent: int):
    STORE_SHEET.append_row([
        str(user_id), item_name, credits_spent, datetime.utcnow().isoformat()
    ])

def update_zone_control(zone
