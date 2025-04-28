# utils/google_sheets.py

import os
import json
import base64
from datetime import datetime
import gspread
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
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# === Worksheet Names ===
WORKSHEETS = {
    'army':           'army',
    'training':       'training',
    'battle_history': 'battle_history',
    'missions':       'player_missions',
    'resources':      'resources',
    'buildings':      'buildings',
    'purchases':      'purchases',
    'building_queue': 'building_queue'
}

# === Worksheet Handles ===
army_ws           = sheet.worksheet(WORKSHEETS['army'])
training_ws       = sheet.worksheet(WORKSHEETS['training'])
battle_ws         = sheet.worksheet(WORKSHEETS['battle_history'])
missions_ws       = sheet.worksheet(WORKSHEETS['missions'])
resources_ws      = sheet.worksheet(WORKSHEETS['resources'])
buildings_ws      = sheet.worksheet(WORKSHEETS['buildings'])
purchases_ws      = sheet.worksheet(WORKSHEETS['purchases'])
building_queue_ws = sheet.worksheet(WORKSHEETS['building_queue'])

# === Army Helpers ===

def load_player_army(player_id):
    try:
        recs = army_ws.get_all_records()
        return {
            row['unit_name']: int(row['quantity'])
            for row in recs if str(row['player_id']) == str(player_id)
        }
    except Exception as e:
        print("load_player_army error:", e)
        return {}

def save_player_army(player_id, army_data):
    try:
        for cell in army_ws.findall(str(player_id)):
            if army_ws.cell(cell.row, 1).value == str(player_id):
                army_ws.delete_row(cell.row)
        for unit, qty in army_data.items():
            if qty > 0:
                army_ws.append_row([player_id, unit, qty])
    except Exception as e:
        print("save_player_army error:", e)

# === Resource Helpers ===

def load_resources(player_id):
    try:
        recs = resources_ws.get_all_records()
        for row in recs:
            if str(row['player_id']) == str(player_id):
                return {
                    'metal':   int(row.get('metal', 0)),
                    'fuel':    int(row.get('fuel', 0)),
                    'crystal': int(row.get('crystal', 0)),
                    'xp':      int(row.get('xp', 0)),
                    'level':   int(row.get('level', 1))
                }
        default = {'metal':0, 'fuel':0, 'crystal':0, 'xp':0, 'level':1}
        resources_ws.append_row([
            player_id,
            default['metal'], default['fuel'], default['crystal'],
            default['xp'],    default['level']
        ])
        return default
    except Exception as e:
        print("load_resources error:", e)
        return {'metal':0, 'fuel':0, 'crystal':0, 'xp':0, 'level':1}

def save_resources(player_id, res):
    try:
        recs = resources_ws.get_all_records()
        for idx, row in enumerate(recs, start=2):
            if str(row['player_id']) == str(player_id):
                resources_ws.update_cell(idx, 2, res['metal'])
                resources_ws.update_cell(idx, 3, res['fuel'])
                resources_ws.update_cell(idx, 4, res['crystal'])
                resources_ws.update_cell(idx, 5, res['xp'])
                resources_ws.update_cell(idx, 6, res['level'])
                return
        resources_ws.append_row([
            player_id,
            res['metal'], res['fuel'], res['crystal'],
            res['xp'],    res['level']
        ])
    except Exception as e:
        print("save_resources error:", e)

# === Purchases & Black Market Helpers ===

def save_purchase(player_id, shop_type, item_id, timestamp=None):
    try:
        ts = timestamp or datetime.now().isoformat()
        purchases_ws.append_row([player_id, shop_type, item_id, ts])
    except Exception as e:
        print("save_purchase error:", e)

def has_purchase(player_id, item_id):
    try:
        recs = purchases_ws.get_all_records()
        return any(
            str(r['player_id']) == str(player_id) and r['item_id'] == item_id
            for r in recs
        )
    except Exception as e:
        print("has_purchase error:", e)
        return False

def unlock_blackmarket(player_id):
    save_purchase(player_id, 'blackmarket_unlock', '', datetime.now().isoformat())

def has_unlocked_blackmarket(player_id):
    try:
        recs = purchases_ws.get_all_records()
        return any(
            str(r['player_id']) == str(player_id) and r['shop_type'] == 'blackmarket_unlock'
            for r in recs
        )
    except Exception as e:
        print("has_unlocked_blackmarket error:", e)
        return False

# === Training Queue Helpers ===

def load_training_queue(player_id):
    try:
        recs = training_ws.get_all_records()
        return {
            idx: {
                'unit_name': row['unit_name'],
                'amount':    int(row['amount']),
                'end_time':  row['end_time']
            }
            for idx, row in enumerate(recs, start=2)
            if str(row['player_id']) == str(player_id)
        }
    except Exception as e:
        print("load_training_queue error:", e)
        return {}

def save_training_task(player_id, unit_name, amount, end_time):
    try:
        training_ws.append_row([
            player_id,
            unit_name,
            amount,
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    except Exception as e:
        print("save_training_task error:", e)

def delete_training_task(row_idx):
    try:
        training_ws.delete_row(row_idx)
    except Exception as e:
        print("delete_training_task error:", e)

# === Battle History Helpers ===

def save_battle_result(player_id, target_id, outcome, rewards, date, battle_log):
    try:
        battle_ws.append_row([player_id, target_id, outcome, rewards, date, battle_log])
    except Exception as e:
        print("save_battle_result error:", e)

def load_battle_history(player_id):
    try:
        recs = battle_ws.get_all_records()
        return [
            {
                'player_id':  r['player_id'],
                'target_id':  r['target_id'],
                'outcome':    r['outcome'],
                'rewards':    r['rewards'],
                'date':       r['date'],
                'battle_log': r['battle_log']
            }
            for r in recs if str(r['player_id']) == str(player_id)
        ]
    except Exception as e:
        print("load_battle_history error:", e)
        return []

def get_battle_wins(player_id):
    try:
        return sum(1 for b in load_battle_history(player_id) if b['outcome'] == 'Victory')
    except Exception as e:
        print("get_battle_wins error:", e)
        return 0

# === Mission Helpers ===

def get_player_missions(player_id, mission_type, date=None):
    try:
        recs = missions_ws.get_all_records()
        out = []
        for idx, row in enumerate(recs, start=2):
            if str(row['player_id']) == str(player_id) and row['type'] == mission_type:
                if mission_type == 'daily' and row['date'] != date:
                    continue
                out.append({
                    'row_idx':    idx,
                    'mission_id': row['mission_id'],
                    'type':       row['type'],
                    'date':       row['date'],
                    'progress':   int(row['progress']),
                    'claimed':    row['claimed'],
                    'rewards':    row['rewards'],
                    'description':row.get('description', '')
                })
        return out
    except Exception as e:
        print("get_player_missions error:", e)
        return []

def get_single_mission(player_id, mission_id):
    try:
        recs = missions_ws.get_all_records()
        for idx, row in enumerate(recs, start=2):
            if (str(row['player_id']) == str(player_id)
             and row['mission_id'] == mission_id):
                return {
                    'row_idx':    idx,
                    'mission_id': row['mission_id'],
                    'type':       row['type'],
                    'date':       row['date'],
                    'progress':   int(row['progress']),
                    'claimed':    row['claimed'],
                    'rewards':    row['rewards'],
                    'description':row.get('description','')
                }
    except Exception as e:
        print("get_single_mission error:", e)
    return None

def save_player_mission(player_id, mission_id, mission_type, date, progress, claimed):
    try:
        missions_ws.append_row([player_id, mission_id, mission_type, date, progress, claimed])
    except Exception as e:
        print("save_player_mission error:", e)

def award_mission_rewards(player_id, rewards):
    try:
        res = load_resources(player_id)
        for k, v in rewards.items():
            if k == 'crystals': res['crystal'] += int(v)
            if k == 'xp':       res['xp']     += int(v)
        save_resources(player_id, res)
    except Exception as e:
        print("award_mission_rewards error:", e)

def mark_mission_claimed(player_id, mission_id):
    try:
        recs = missions_ws.get_all_records()
        for idx, row in enumerate(recs, start=2):
            if (str(row['player_id']) == str(player_id)
             and row['mission_id'] == mission_id):
                missions_ws.update_cell(idx, 6, True)
                break
    except Exception as e:
        print("mark_mission_claimed error:", e)

# === Building Queue Helpers ===

def load_building_queue(player_id):
    try:
        recs = building_queue_ws.get_all_records()
        queue = {}
        for idx, row in enumerate(recs, start=2):
            if str(row['player_id']) == str(player_id):
                queue[idx] = {
                    'building_name': row['building_name'],
                    'start_time':    row['start_time'],
                    'end_time':      row['end_time']
                }
        return queue
    except Exception as e:
        print("load_building_queue error:", e)
        return {}

def save_building_task(player_id, building_name, start_time, end_time):
    try:
        building_queue_ws.append_row([
            player_id,
            building_name,
            start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time.strftime("%Y-%m-%d %H:%M:%S")
        ])
    except Exception as e:
        print("save_building_task error:", e)

def delete_building_task(row_idx):
    try:
        building_queue_ws.delete_row(row_idx)
    except Exception as e:
        print("delete_building_task error:", e)

# === Building Level Helpers ===

def save_building_level(player_id, building_name, new_level):
    try:
        for cell in buildings_ws.findall(str(player_id)):
            if buildings_ws.cell(cell.row, 2).value == building_name:
                buildings_ws.delete_row(cell.row)
        buildings_ws.append_row([player_id, building_name, new_level])
    except Exception as e:
        print("save_building_level error:", e)

# === Miscellaneous Queries ===

def get_training_total(player_id, unit, amount):
    try:
        return load_player_army(player_id).get(unit, 0)
    except:
        return 0

def get_mined_total(player_id, resource, amount):
    try:
        return load_resources(player_id).get(resource, 0)
    except:
        return 0

def get_attack_count(player_id):
    try:
        recs = battle_ws.get_all_records()
        return sum(1 for r in recs if str(r['player_id']) == str(player_id))
    except:
        return 0

def get_building_level(player_id, building_name):
    try:
        recs = buildings_ws.get_all_records()
        for row in recs:
            if (str(row['player_id']) == str(player_id)
             and row['building_name'] == building_name):
                return int(row['level'])
    except Exception as e:
        print("get_building_level error:", e)
    return 1
