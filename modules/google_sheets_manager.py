"""
Google Sheets Manager for SkyHustle 2
Handles connection, tab creation, and all game data operations
"""

import os
import json
import base64
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional

SHEET_TABS = {
    'Players': [
        'player_id', 'name', 'level', 'xp', 'resources', 'army', 'alliance', 'hustlecoins', 'achievements', 'last_active', 'bag'
    ],
    'Alliances': [
        'alliance_id', 'name', 'level', 'xp', 'members', 'leader', 'created_at', 'perks', 'war_history', 'diplomacy', 'resources'
    ],
    'AllianceWars': [
        'war_id', 'attacker_id', 'defender_id', 'start_time', 'end_time', 'result', 'score', 'details'
    ],
    'ShopTransactions': [
        'transaction_id', 'player_id', 'item_id', 'item_name', 'quantity', 'cost', 'currency', 'timestamp'
    ],
    'BlackMarketTransactions': [
        'transaction_id', 'player_id', 'item_id', 'item_name', 'quantity', 'cost', 'currency', 'timestamp'
    ],
    'DailyRewards': [
        'claim_id', 'player_id', 'date', 'reward', 'claimed_at'
    ],
    'Achievements': [
        'achievement_id', 'player_id', 'achievement', 'date', 'details'
    ],
    'Logs': [
        'log_id', 'timestamp', 'level', 'event', 'details'
    ]
}

class GoogleSheetsManager:
    def __init__(self):
        creds_b64 = os.getenv('BASE64_CREDS')
        sheet_id = os.getenv('SHEET_ID')
        if not creds_b64 or not sheet_id:
            raise ValueError("Missing BASE64_CREDS or SHEET_ID in environment variables.")
        creds_json = base64.b64decode(creds_b64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        self.gc = gspread.authorize(creds)
        self.sheet = self.gc.open_by_key(sheet_id)
        # Ensure all tabs exist with correct headers
        for tab, headers in SHEET_TABS.items():
            self.ensure_headers(tab, headers)

    def _get_or_create_worksheet(self, title: str, headers: List[str]):
        try:
            ws = self.sheet.worksheet(title)
            # Check headers
            current_headers = ws.row_values(1)
            if current_headers != headers:
                ws.delete_rows(1)
                ws.insert_row(headers, 1)
            return ws
        except gspread.WorksheetNotFound:
            ws = self.sheet.add_worksheet(title=title, rows=1000, cols=len(headers))
            ws.insert_row(headers, 1)
            return ws

    def ensure_headers(self, tab: str, headers: List[str]):
        self._get_or_create_worksheet(tab, headers)

    def get_worksheet(self, tab: str) -> gspread.Worksheet:
        headers = SHEET_TABS[tab]
        return self._get_or_create_worksheet(tab, headers)

    # --- CRUD for Players ---
    def get_all_players(self):
        ws = self.get_worksheet('Players')
        return ws.get_all_records()

    def get_player(self, player_id):
        ws = self.get_worksheet('Players')
        for row in ws.get_all_records():
            if str(row.get('player_id')) == str(player_id):
                return row
        return None

    def upsert_player(self, player_data):
        ws = self.get_worksheet('Players')
        player_id = str(player_data['player_id'])
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get('player_id')) == player_id:
                cell_list = ws.range(f'A{idx}:K{idx}')
                for i, key in enumerate(SHEET_TABS['Players']):
                    if key in player_data:
                        cell_list[i].value = player_data[key]
                ws.update_cells(cell_list)
                return
        values = [player_data.get(key, '') for key in SHEET_TABS['Players']]
        ws.append_row(values)

    # --- CRUD for Alliances ---
    def get_all_alliances(self):
        ws = self.get_worksheet('Alliances')
        return ws.get_all_records()

    def get_alliance(self, alliance_id):
        ws = self.get_worksheet('Alliances')
        for row in ws.get_all_records():
            if str(row.get('alliance_id')) == str(alliance_id):
                return row
        return None

    def upsert_alliance(self, alliance_data):
        ws = self.get_worksheet('Alliances')
        alliance_id = str(alliance_data['alliance_id'])
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get('alliance_id')) == alliance_id:
                cell_list = ws.range(f'A{idx}:K{idx}')
                for i, key in enumerate(SHEET_TABS['Alliances']):
                    if key in alliance_data:
                        cell_list[i].value = alliance_data[key]
                ws.update_cells(cell_list)
                return
        values = [alliance_data.get(key, '') for key in SHEET_TABS['Alliances']]
        ws.append_row(values)

    # --- CRUD for AllianceWars ---
    def log_alliance_war(self, war_data):
        ws = self.get_worksheet('AllianceWars')
        values = [war_data.get(key, '') for key in SHEET_TABS['AllianceWars']]
        ws.append_row(values)

    # --- CRUD for ShopTransactions ---
    def log_shop_transaction(self, tx_data):
        ws = self.get_worksheet('ShopTransactions')
        values = [tx_data.get(key, '') for key in SHEET_TABS['ShopTransactions']]
        ws.append_row(values)

    # --- CRUD for BlackMarketTransactions ---
    def log_blackmarket_transaction(self, tx_data):
        ws = self.get_worksheet('BlackMarketTransactions')
        values = [tx_data.get(key, '') for key in SHEET_TABS['BlackMarketTransactions']]
        ws.append_row(values)

    # --- CRUD for DailyRewards ---
    def log_daily_reward(self, reward_data):
        ws = self.get_worksheet('DailyRewards')
        values = [reward_data.get(key, '') for key in SHEET_TABS['DailyRewards']]
        ws.append_row(values)

    # --- CRUD for Achievements ---
    def log_achievement(self, achievement_data):
        ws = self.get_worksheet('Achievements')
        values = [achievement_data.get(key, '') for key in SHEET_TABS['Achievements']]
        ws.append_row(values)

    # --- CRUD for Logs ---
    def log_event(self, log_data):
        ws = self.get_worksheet('Logs')
        values = [log_data.get(key, '') for key in SHEET_TABS['Logs']]
        ws.append_row(values) 