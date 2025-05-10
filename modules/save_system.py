# bot/modules/save_system.py

from sheets_service import get_rows, update_row, append_row

def save_player_data(player_id, data):
    players = get_rows("Players")
    for idx, row in enumerate(players[1:], start=1):
        if row[0] == player_id:
            # Update existing player row with new data
            updated_row = row[:8]  # Keep first 8 columns unchanged
            updated_row.extend([
                data.get("alliance", ""),
                data.get("global_rank", "?")
            ])
            update_row("Players", idx, updated_row)
            return
    # If player not found, append new row
    new_row = [
        player_id,
        data.get("name", "Unknown Commander"),
        data.get("credits", 1000),
        data.get("minerals", 500),
        data.get("energy", 200),
        data.get("skybucks", 0),
        data.get("experience", 0),
        data.get("level", 1),
        data.get("last_login", int(time.time())),
        data.get("alliance", ""),
        data.get("global_rank", "?")
    ]
    append_row("Players", new_row)

def save_building_data(player_id, building_name, data):
    buildings = get_rows("Buildings")
    for idx, row in enumerate(buildings[1:], start=1):
        if row[0] == player_id and row[1] == building_name:
            updated_row = [
                player_id,
                building_name,
                data.get("level", 1),
                data.get("production", 10)
            ]
            update_row("Buildings", idx, updated_row)
            return
    new_row = [
        player_id,
        building_name,
        data.get("level", 1),
        data.get("production", 10)
    ]
    append_row("Buildings", new_row)

def save_unit_data(player_id, unit_name, count):
    units = get_rows("Units")
    for idx, row in enumerate(units[1:], start=1):
        if row[0] == player_id and row[1] == unit_name:
            updated_row = [
                player_id,
                unit_name,
                count
            ]
            update_row("Units", idx, updated_row)
            return
    new_row = [
        player_id,
        unit_name,
        count
    ]
    append_row("Units", new_row)

def load_player_data(player_id):
    players = get_rows("Players")
    for row in players[1:]:
        if row[0] == player_id:
            return {
                "name": row[1],
                "credits": int(row[2]),
                "minerals": int(row[3]),
                "energy": int(row[4]),
                "skybucks": int(row[5]),
                "experience": int(row[6]),
                "level": int(row[7]),
                "last_login": int(row[8]) if len(row) > 8 else int(time.time()),
                "alliance": row[9] if len(row) > 9 else "",
                "global_rank": row[10] if len(row) > 10 else "?"
            }
    return {
        "name": "Unknown Commander",
        "credits": 1000,
        "minerals": 500,
        "energy": 200,
        "skybucks": 0,
        "experience": 0,
        "level": 1,
        "last_login": int(time.time()),
        "alliance": "",
        "global_rank": "?"
    }

def load_buildings_data(player_id):
    buildings = get_rows("Buildings")
    building_info = {}
    for row in buildings[1:]:
        if row[0] == player_id:
            building_info[row[1]] = {
                "level": int(row[2]),
                "production": int(row[3])
            }
    return building_info

def load_units_data(player_id):
    units = get_rows("Units")
    unit_info = {}
    for row in units[1:]:
        if row[0] == player_id:
            unit_info[row[1]] = int(row[2])
    return unit_info
