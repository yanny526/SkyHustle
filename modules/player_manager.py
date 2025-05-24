"""
Player Manager Module
Handles player profiles, names, and data storage (per-player)
"""

import re
from typing import Dict, Optional, List
import json
import os
import time
from modules.google_sheets_manager import GoogleSheetsManager

class PlayerManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()
        self.headers = [
            'player_id', 'name', 'level', 'xp', 'resources', 'army', 'alliance', 'hustlecoins', 'achievements', 'last_active', 'bag'
        ]
        self.sheets.ensure_headers('Players', self.headers)

    def get_player(self, player_id):
        return self.sheets.get_player(player_id)

    def upsert_player(self, player_data):
        self.sheets.upsert_player(player_data)

    def get_all_players(self):
        return self.sheets.get_all_players()

    def create_player(self, player_id: str) -> Dict:
        if player_id in [p['player_id'] for p in self.sheets.get_all_players()]:
            return {'success': False, 'message': 'Player already exists'}
        self.sheets.upsert_player({
            'player_id': player_id,
            'name': f"Player_{player_id[:8]}",
            'level': 1,
            'xp': 0,
            'resources': {},
            'army': {},
            'alliance': '',
            'hustlecoins': 0,
            'achievements': [],
            'last_active': time.time(),
            'bag': []
        })
        return {'success': True}

    def set_player_name(self, player_id: str, name: str) -> Dict:
        if not self._is_valid_name(name):
            return {
                'success': False,
                'message': 'Invalid name. Use only letters, numbers, and spaces (3-20 characters)'
            }
        if name.lower() in [p['name'].lower() for p in self.sheets.get_all_players()]:
            return {'success': False, 'message': 'This name is already taken'}
        player = self.sheets.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found'}
        player['name'] = name
        self.sheets.upsert_player(player)
        return {'success': True}

    def get_player_name(self, player_id: str) -> str:
        player = self.sheets.get_player(player_id)
        return player['name'] if player else f"Player_{player_id[:8]}"

    def get_player_profile(self, player_id: str) -> Dict:
        player = self.sheets.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found'}
        return {
            'success': True,
            'name': self.get_player_name(player_id),
            'level': player['level'],
            'experience': player['xp'],
            'created_at': player['last_active'],
            'last_login': player['last_active']
        }

    def update_last_login(self, player_id: str):
        player = self.sheets.get_player(player_id)
        if player:
            player['last_active'] = time.time()
            self.sheets.upsert_player(player)

    def add_experience(self, player_id: str, amount: int):
        player = self.sheets.get_player(player_id)
        if player:
            player['xp'] += amount
            self.sheets.upsert_player(player)
            self._check_level_up(player_id)

    def _check_level_up(self, player_id: str):
        player = self.sheets.get_player(player_id)
        if not player:
            return
        current_level = player['level']
        experience = player['xp']
        required_exp = current_level * 1000
        if experience >= required_exp:
            player['level'] = current_level + 1
            player['xp'] = experience - required_exp
            self.sheets.upsert_player(player)

    def _is_valid_name(self, name: str) -> bool:
        pattern = r'^[a-zA-Z0-9\s]{3,20}$'
        return bool(re.match(pattern, name))

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        players = []
        for player in self.get_all_players():
            players.append({
                'id': player['player_id'],
                'name': player['name'],
                'level': player['level'],
                'experience': player['xp']
            })
        players.sort(key=lambda x: (x['level'], x['experience']), reverse=True)
        return players[:limit]

    def get_hustlecoins(self, player_id: str) -> int:
        player = self.get_player(player_id)
        return player.get('hustlecoins', 0) if player else 0

    def add_hustlecoins(self, player_id: str, amount: int) -> bool:
        player = self.get_player(player_id)
        if not player:
            return False
        player['hustlecoins'] = player.get('hustlecoins', 0) + amount
        self.upsert_player(player)
        return True

    def spend_hustlecoins(self, player_id: str, amount: int) -> bool:
        player = self.get_player(player_id)
        if not player or player.get('hustlecoins', 0) < amount:
            return False
        player['hustlecoins'] -= amount
        self.upsert_player(player)
        return True 