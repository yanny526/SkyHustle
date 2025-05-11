import os
import gspread
import base64
import json
import time
import random
from google.oauth2.service_account import Credentials

class SimpleCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        entry = self._cache.get(key)
        if entry and entry['expires_at'] > time.time():
            return entry['value']
        elif entry:
            del self._cache[key]
        return None

    def set(self, key, value, ttl=3600):
        self._cache[key] = {'value': value, 'expires_at': time.time() + ttl}

class SheetsService:
    REQUIRED_SHEETS = {
        "Players": [
            "player_id", "display_name", "credits", "minerals", "energy", "skybucks", "experience", "tutorial_completed", "last_login"
        ],
        "Buildings": [
            "player_id", "structure_id", "status"
        ],
        "Units": [
            "player_id", "unit_type", "count", "status"
        ],
        "Alliances": [
            "alliance_id", "name", "leader_id", "join_code", "created_at"
        ],
        "AllianceMembers": [
            "alliance_id", "player_id", "role", "joined_at"
        ],
        "Research": [
            "player_id", "tech_id", "unlocked_at"
        ],
        "Wars": [
            "war_id", "alliance1_id", "alliance2_id", "status", "created_at"
        ],
        "Daily": [
            "player_id", "last_claimed", "streak"
        ]
    }
    UNIT_COSTS = {
        "drone": {"credits": 100, "minerals": 50, "energy": 10},
        "mech": {"credits": 500, "minerals": 200, "energy": 50},
        "jet": {"credits": 1000, "minerals": 500, "energy": 100},
    }
    TECH_TREE = {
        "plasma": {"name": "Plasma Weapons", "prereq": []},
        "shields": {"name": "Energy Shields", "prereq": ["plasma"]},
    }
    ACHIEVEMENT_LIST = [
        {"id": "first_build", "name": "First Construction", "desc": "Build your first structure", "reward": 100},
        {"id": "first_win", "name": "First Victory", "desc": "Win your first battle", "reward": 200},
        # Add more as needed
    ]
    def __init__(self):
        base64_creds = os.getenv("BASE64_CREDS")
        if not base64_creds:
            raise RuntimeError("BASE64_CREDS environment variable not set.")
        creds_json = base64.b64decode(base64_creds).decode()
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
        ])
        self.gc = gspread.authorize(creds)
        self.sheet_id = os.getenv("SHEET_ID")
        if not self.sheet_id:
            raise RuntimeError("SHEET_ID environment variable not set.")
        self.sheet = self.gc.open_by_key(self.sheet_id)
        self.cache = SimpleCache()
        self._ensure_sheets_exist()
        self.players_ws = self.sheet.worksheet("Players")

    def _ensure_sheets_exist(self):
        existing_titles = [ws.title for ws in self.sheet.worksheets()]
        for title, headers in self.REQUIRED_SHEETS.items():
            if title not in existing_titles:
                ws = self.sheet.add_worksheet(title=title, rows=100, cols=len(headers))
                ws.append_row(headers)
            else:
                ws = self.sheet.worksheet(title)
                current_headers = ws.row_values(1)
                if current_headers != headers:
                    ws.delete_rows(1)
                    ws.insert_row(headers, 1)

    # Player methods
    async def get_player(self, player_id: str):
        cache_key = f"player:{player_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        try:
            records = self.players_ws.get_all_records()
            for row in records:
                if str(row.get("player_id")) == str(player_id):
                    self.cache.set(cache_key, row, ttl=300)
                    return row
        except Exception as e:
            print(f"Error fetching player: {e}")
        return None

    async def save_player(self, player_data: dict):
        player_id = player_data.get("player_id")
        if not player_id:
            raise ValueError("player_data must include player_id")
        try:
            records = self.players_ws.get_all_records()
            for idx, row in enumerate(records, start=2):
                if str(row.get("player_id")) == str(player_id):
                    cell_list = self.players_ws.range(f"A{idx}:I{idx}")
                    headers = self.players_ws.row_values(1)
                    for i, header in enumerate(headers):
                        if header in player_data:
                            cell_list[i].value = player_data[header]
                    self.players_ws.update_cells(cell_list)
                    self.cache.set(f"player:{player_id}", player_data, ttl=300)
                    return
            values = [player_data.get(h, "") for h in self.players_ws.row_values(1)]
            self.players_ws.append_row(values)
            self.cache.set(f"player:{player_id}", player_data, ttl=300)
        except Exception as e:
            print(f"Error saving player: {e}")

    # Unit methods
    async def get_unit(self, player_id: str, unit_type: str):
        try:
            ws = self.sheet.worksheet("Units")
            records = ws.get_all_records()
            for row in records:
                if str(row.get("player_id")) == str(player_id) and row.get("unit_type") == unit_type:
                    return row
            return None
        except Exception as e:
            print(f"Error fetching unit: {e}")
            return None

    async def save_unit(self, player_id: str, unit_type: str, count: int):
        try:
            ws = self.sheet.worksheet("Units")
            records = ws.get_all_records()
            for idx, row in enumerate(records, start=2):
                if str(row.get("player_id")) == str(player_id) and row.get("unit_type") == unit_type:
                    current_count = int(row.get("count", 0))
                    ws.update_cell(idx, ws.find("count").col, current_count + count)
                    return
            headers = ws.row_values(1)
            values = [player_id if h == "player_id" else unit_type if h == "unit_type" else count if h == "count" else "" for h in headers]
            ws.append_row(values)
        except Exception as e:
            print(f"Error saving unit: {e}")

    async def deduct_resources(self, player_id: str, cost: dict):
        player = await self.get_player(player_id)
        if not player:
            return False, "Player not found."
        for res, amount in cost.items():
            if int(player.get(res, 0)) < amount:
                return False, f"Not enough {res}."
        for res, amount in cost.items():
            player[res] = int(player.get(res, 0)) - amount
        await self.save_player(player)
        return True, ""

    # Alliance methods
    async def create_alliance(self, name: str, leader_id: str):
        ws = self.sheet.worksheet("Alliances")
        alliance_id = str(int(time.time() * 1000))
        join_code = str(int(time.time()))[-6:]
        ws.append_row([alliance_id, name, leader_id, join_code, str(int(time.time()))])
        # Add leader as member
        ws_mem = self.sheet.worksheet("AllianceMembers")
        ws_mem.append_row([alliance_id, leader_id, "leader", str(int(time.time()))])
        return alliance_id, join_code

    async def join_alliance(self, player_id: str, join_code: str):
        ws = self.sheet.worksheet("Alliances")
        alliances = ws.get_all_records()
        alliance = next((a for a in alliances if a.get("join_code") == join_code), None)
        if not alliance:
            return False, "Alliance not found."
        ws_mem = self.sheet.worksheet("AllianceMembers")
        ws_mem.append_row([alliance["alliance_id"], player_id, "member", str(int(time.time()))])
        return True, alliance["name"]

    async def get_alliance_info(self, player_id: str):
        ws_mem = self.sheet.worksheet("AllianceMembers")
        ws = self.sheet.worksheet("Alliances")
        members = ws_mem.get_all_records()
        alliances = ws.get_all_records()
        member = next((m for m in members if m.get("player_id") == player_id), None)
        if not member:
            return None
        alliance = next((a for a in alliances if a.get("alliance_id") == member["alliance_id"]), None)
        if not alliance:
            return None
        member_count = sum(1 for m in members if m.get("alliance_id") == alliance["alliance_id"])
        return {
            "name": alliance["name"],
            "leader_id": alliance["leader_id"],
            "member_count": member_count,
            "join_code": alliance["join_code"]
        }

    # PvP/Scan/Attack
    async def get_pvp_targets(self, player_id: str, power: int):
        ws = self.sheet.worksheet("Players")
        players = ws.get_all_records()
        min_power = int(power * 0.9)
        max_power = int(power * 1.1)
        return [p for p in players if p.get("player_id") != player_id and min_power <= int(p.get("experience", 0)) <= max_power]

    async def log_attack(self, attacker_id: str, target_id: str, result: dict):
        ws = self.sheet.worksheet("Wars")
        ws.append_row([str(int(time.time() * 1000)), attacker_id, target_id, json.dumps(result), str(int(time.time()))])

    # Research
    async def get_research(self, player_id: str):
        ws = self.sheet.worksheet("Research")
        return [r for r in ws.get_all_records() if r.get("player_id") == player_id]

    async def unlock_tech(self, player_id: str, tech_id: str):
        ws = self.sheet.worksheet("Research")
        ws.append_row([player_id, tech_id, str(int(time.time()))])

    # Daily
    async def get_daily(self, player_id: str):
        ws = self.sheet.worksheet("Daily")
        records = ws.get_all_records()
        for row in records:
            if row.get("player_id") == player_id:
                return row
        return None

    async def update_daily(self, player_id: str, streak: int):
        ws = self.sheet.worksheet("Daily")
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if row.get("player_id") == player_id:
                ws.update_cell(idx, ws.find("streak").col, streak)
                ws.update_cell(idx, ws.find("last_claimed").col, str(int(time.time())))
                return
        ws.append_row([player_id, str(int(time.time())), streak])

    async def get_achievements(self, player_id: str):
        ws = self.sheet.worksheet("Achievements")
        return [a for a in ws.get_all_records() if a.get("player_id") == player_id]

    async def claim_achievement(self, player_id: str, achievement_id: str):
        ws = self.sheet.worksheet("Achievements")
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if row.get("player_id") == player_id and row.get("achievement_id") == achievement_id:
                if row.get("claimed") == "1":
                    return False, "Already claimed."
                ws.update_cell(idx, ws.find("claimed").col, "1")
                # Grant reward
                player = await self.get_player(player_id)
                for a in self.ACHIEVEMENT_LIST:
                    if a["id"] == achievement_id:
                        player["credits"] = int(player.get("credits", 0)) + a["reward"]
                        await self.save_player(player)
                        return True, f"Claimed {a['name']}! +{a['reward']} credits."
        return False, "Achievement not found or not completed."

    async def get_active_events(self):
        ws = self.sheet.worksheet("Events")
        now = int(time.time())
        return [
            e for e in ws.get_all_records()
            if int(e.get("start_time", 0)) <= now <= int(e.get("end_time", 0))
        ]

    async def join_event(self, player_id: str, event_id: str):
        ws = self.sheet.worksheet("Events")
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if row.get("event_id") == event_id:
                participants = row.get("participants", "")
                if player_id in participants.split(","):
                    return False, "Already joined."
                new_participants = participants + "," + player_id if participants else player_id
                ws.update_cell(idx, ws.find("participants").col, new_participants)
                return True, "Joined event!"
        return False, "Event not found."

    async def get_leaderboard(self, scope="global", alliance_id=None, page=1, page_size=10):
        ws = self.sheet.worksheet("Players")
        players = ws.get_all_records()
        if scope == "alliance" and alliance_id:
            # Filter by alliance
            ws_mem = self.sheet.worksheet("AllianceMembers")
            members = ws_mem.get_all_records()
            member_ids = [m["player_id"] for m in members if m["alliance_id"] == alliance_id]
            players = [p for p in players if p["player_id"] in member_ids]
        # For now, only global and alliance scopes are implemented
        players = sorted(players, key=lambda x: int(x.get("experience", 0)), reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return players[start:end], len(players)

    async def get_stats(self):
        ws = self.sheet.worksheet("Players")
        players = ws.get_all_records()
        ws_units = self.sheet.worksheet("Units")
        units = ws_units.get_all_records()
        ws_alliances = self.sheet.worksheet("Alliances")
        alliances = ws_alliances.get_all_records()
        return {
            "players": len(players),
            "units": sum(int(u.get("count", 0)) for u in units),
            "alliances": len(alliances)
        }

    async def create_war(self, alliance1_id: str, alliance2_id: str):
        ws = self.sheet.worksheet("AllianceWars")
        war_id = str(int(time.time() * 1000))
        ws.append_row([war_id, alliance1_id, alliance2_id, "pending", str(int(time.time())), ""])
        return war_id

    async def get_active_wars(self, alliance_id: str):
        ws = self.sheet.worksheet("AllianceWars")
        return [
            w for w in ws.get_all_records()
            if w.get("status") in ["pending", "active"] and (w.get("alliance1_id") == alliance_id or w.get("alliance2_id") == alliance_id)
        ]

    async def deploy_to_war(self, war_id: str, player_id: str, units_committed: int):
        ws = self.sheet.worksheet("WarDeployments")
        ws.append_row([war_id, player_id, units_committed, 0, str(int(time.time()))])

    async def get_war_status(self, war_id: str):
        ws = self.sheet.worksheet("AllianceWars")
        wars = ws.get_all_records()
        war = next((w for w in wars if w.get("war_id") == war_id), None)
        if not war:
            return None
        ws_dep = self.sheet.worksheet("WarDeployments")
        deployments = [d for d in ws_dep.get_all_records() if d.get("war_id") == war_id]
        return {"war": war, "deployments": deployments}

    async def get_active_missions(self):
        ws = self.sheet.worksheet("Missions")
        return [m for m in ws.get_all_records() if m.get("active") == "1"]

    async def attempt_mission(self, player_id: str, mission_id: str):
        ws = self.sheet.worksheet("Missions")
        missions = ws.get_all_records()
        mission = next((m for m in missions if m.get("mission_id") == mission_id), None)
        if not mission:
            return False, "Mission not found."
        player = await self.get_player(player_id)
        power = int(player.get("experience", 0))
        required = int(mission.get("required_power", 0))
        success = power >= required or random.random() < 0.5
        ws_attempts = self.sheet.worksheet("MissionAttempts")
        ws_attempts.append_row([mission_id, player_id, "1" if success else "0", str(int(time.time()))])
        if success:
            player["credits"] = int(player.get("credits", 0)) + int(mission.get("reward", 0))
            await self.save_player(player)
            return True, f"Mission success! +{mission.get('reward', 0)} credits."
        else:
            return False, "Mission failed. Try again later."