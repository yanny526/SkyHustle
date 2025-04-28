import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === Google Sheet Setup ===
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"
WORKSHEETS = {
    'army': 'army',
    'training': 'training',
    'battle_history': 'battle_history',
    'missions': 'player_missions',
    'resources': 'resources',
    'buildings': 'buildings',
    'purchases': 'purchases'
}

# Authorize
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# Worksheet handles
army_ws         = sheet.worksheet(WORKSHEETS['army'])
resources_ws    = sheet.worksheet(WORKSHEETS['resources'])
purchases_ws    = sheet.worksheet(WORKSHEETS['purchases'])

# === Army Helpers ===

def load_player_army(player_id):
    try:
        records = army_ws.get_all_records()
        army = {}
        for row in records:
            if str(row['player_id']) == str(player_id):
                army[row['unit_name']] = int(row['quantity'])
        return army
    except Exception as e:
        print("load_player_army error:", e)
        return {}

def save_player_army(player_id, army_data):
    try:
        # Delete old rows
        for cell in army_ws.findall(str(player_id)):
            if army_ws.cell(cell.row, 1).value == str(player_id):
                army_ws.delete_row(cell.row)
        # Append current
        for unit, qty in army_data.items():
            if qty > 0:
                army_ws.append_row([player_id, unit, qty])
    except Exception as e:
        print("save_player_army error:", e)

# === Resource Helpers ===

def load_resources(player_id):
    try:
        records = resources_ws.get_all_records()
        for row in records:
            if str(row['player_id']) == str(player_id):
                return {
                    'metal':   int(row.get('metal', 0)),
                    'fuel':    int(row.get('fuel', 0)),
                    'crystal': int(row.get('crystal', 0)),
                    'xp':      int(row.get('xp', 0)),
                    'level':   int(row.get('level', 1))
                }
        # Not found → create default
        default = {'metal':0,'fuel':0,'crystal':0,'xp':0,'level':1}
        resources_ws.append_row([
            player_id,
            default['metal'], default['fuel'], default['crystal'],
            default['xp'],    default['level']
        ])
        return default
    except Exception as e:
        print("load_resources error:", e)
        return {'metal':0,'fuel':0,'crystal':0,'xp':0,'level':1}

def save_resources(player_id, res):
    try:
        records = resources_ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row['player_id']) == str(player_id):
                resources_ws.update_cell(idx, 2, res['metal'])
                resources_ws.update_cell(idx, 3, res['fuel'])
                resources_ws.update_cell(idx, 4, res['crystal'])
                resources_ws.update_cell(idx, 5, res['xp'])
                resources_ws.update_cell(idx, 6, res['level'])
                return
        # Not found → append
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
        records = purchases_ws.get_all_records()
        return any(
            str(r['player_id']) == str(player_id) and r['item_id'] == item_id
            for r in records
        )
    except Exception as e:
        print("has_purchase error:", e)
        return False

def unlock_blackmarket(player_id):
    # Record the unlock as a special purchase
    save_purchase(player_id, 'blackmarket_unlock', '', datetime.now().isoformat())

def has_unlocked_blackmarket(player_id):
    try:
        records = purchases_ws.get_all_records()
        return any(
            str(r['player_id']) == str(player_id) and r['shop_type'] == 'blackmarket_unlock'
            for r in records
        )
    except Exception as e:
        print("has_unlocked_blackmarket error:", e)
        return False
# === Continued google_sheets.py (Part 2) ===

# Worksheet handles
training_ws    = sheet.worksheet(WORKSHEETS['training'])
missions_ws    = sheet.worksheet(WORKSHEETS['missions'])
battle_ws      = sheet.worksheet(WORKSHEETS['battle_history'])
buildings_ws   = sheet.worksheet(WORKSHEETS['buildings'])

# === Training Queue Helpers ===

def load_training_queue(player_id):
    try:
        records = training_ws.get_all_records()
        queue = {}
        for idx, row in enumerate(records, start=2):
            if str(row['player_id']) == str(player_id):
                queue[idx] = {
                    'unit_name': row['unit_name'],
                    'amount': int(row['amount']),
                    'end_time': row['end_time']
                }
        return queue
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
        records = battle_ws.get_all_records()
        return [
            {
                'player_id': row['player_id'],
                'target_id': row['target_id'],
                'outcome': row['outcome'],
                'rewards': row['rewards'],
                'date': row['date'],
                'battle_log': row['battle_log']
            }
            for row in records if str(row['player_id']) == str(player_id)
        ]
    except Exception as e:
        print("load_battle_history error:", e)
        return []

def get_battle_wins(player_id):
    try:
        history = load_battle_history(player_id)
        return sum(1 for b in history if b['outcome'] == 'Victory')
    except Exception as e:
        print("get_battle_wins error:", e)
        return 0

# === Mission Helpers ===

def get_player_missions(player_id, mission_type, date=None):
    try:
        records = missions_ws.get_all_records()
        result = []
        for idx, row in enumerate(records, start=2):
            if str(row['player_id']) == str(player_id) and row['type'] == mission_type:
                if mission_type == 'daily' and row['date'] != date:
                    continue
                result.append({
                    'row_idx': idx,
                    'mission_id': row['mission_id'],
                    'type': row['type'],
                    'date': row['date'],
                    'progress': int(row['progress']),
                    'claimed': row['claimed'],
                    'rewards': row['rewards'],
                    'description': row.get('description', '')
                })
        return result
    except Exception as e:
        print("get_player_missions error:", e)
        return []

def get_single_mission(player_id, mission_id):
    try:
        records = missions_ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row['player_id']) == str(player_id) and row['mission_id'] == mission_id:
                return {
                    'row_idx': idx,
                    'mission_id': row['mission_id'],
                    'type': row['type'],
                    'date': row['date'],
                    'progress': int(row['progress']),
                    'claimed': row['claimed'],
                    'rewards': row['rewards'],
                    'description': row.get('description', '')
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
            if k == 'crystals':
                res['crystal'] += int(v)
            elif k == 'xp':
                res['xp'] += int(v)
        save_resources(player_id, res)
    except Exception as e:
        print("award_mission_rewards error:", e)

def mark_mission_claimed(player_id, mission_id):
    try:
        records = missions_ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row['player_id']) == str(player_id) and row['mission_id'] == mission_id:
                missions_ws.update_cell(idx, 6, True)
                break
    except Exception as e:
        print("mark_mission_claimed error:", e)

# === Other Helpers ===

def get_training_total(player_id, unit, amount):
    try:
        army = load_player_army(player_id)
        return army.get(unit, 0)
    except:
        return 0

def get_mined_total(player_id, resource, amount):
    try:
        res = load_resources(player_id)
        return res.get(resource, 0)
    except:
        return 0

def get_attack_count(player_id):
    try:
        records = battle_ws.get_all_records()
        return sum(1 for row in records if str(row['player_id']) == str(player_id))
    except:
        return 0

def get_building_level(player_id, building_name):
    try:
        records = buildings_ws.get_all_records()
        for row in records:
            if str(row['player_id']) == str(player_id) and row['building_name'] == building_name:
                return int(row['level'])
    except Exception as e:
        print("get_building_level error:", e)
    return 1
