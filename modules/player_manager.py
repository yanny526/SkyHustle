"""
Player Manager Module
Handles player profiles, names, and data storage
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
        """Create a new player profile"""
        if player_id in self.sheets.get_all_players():
            return {'success': False, 'message': 'Player already exists'}

        self.sheets.upsert_player({
            'player_id': player_id,
            'name': f"Player_{player_id[:8]}",
            'level': 1,
            'xp': 0,
            'resources': 0,
            'army': [],
            'alliance': '',
            'hustlecoins': 0,
            'achievements': [],
            'last_active': time.time(),
            'bag': []
        })
        return {'success': True}

    def set_player_name(self, player_id: str, name: str) -> Dict:
        """Set player's display name"""
        # Validate name
        if not self._is_valid_name(name):
            return {
                'success': False,
                'message': 'Invalid name. Use only letters, numbers, and spaces (3-20 characters)'
            }

        # Check if name is taken
        if name.lower() in [p['name'].lower() for p in self.sheets.get_all_players()]:
            return {'success': False, 'message': 'This name is already taken'}

        # Set name
        self.sheets.upsert_player({
            'player_id': player_id,
            'name': name,
            'level': self.sheets.get_player(player_id)['level'],
            'xp': self.sheets.get_player(player_id)['xp'],
            'resources': self.sheets.get_player(player_id)['resources'],
            'army': self.sheets.get_player(player_id)['army'],
            'alliance': self.sheets.get_player(player_id)['alliance'],
            'hustlecoins': self.sheets.get_player(player_id)['hustlecoins'],
            'achievements': self.sheets.get_player(player_id)['achievements'],
            'last_active': self.sheets.get_player(player_id)['last_active'],
            'bag': self.sheets.get_player(player_id)['bag']
        })
        return {'success': True}

    def get_player_name(self, player_id: str) -> str:
        """Get player's display name"""
        player = self.sheets.get_player(player_id)
        return player['name'] if player else f"Player_{player_id[:8]}"

    def get_player_profile(self, player_id: str) -> Dict:
        """Get player's profile information"""
        if player_id not in self.sheets.get_all_players():
            return {'success': False, 'message': 'Player not found'}

        player = self.sheets.get_player(player_id)
        return {
            'success': True,
            'name': self.get_player_name(player_id),
            'level': player['level'],
            'experience': player['xp'],
            'created_at': player['last_active'],
            'last_login': player['last_active']
        }

    def update_last_login(self, player_id: str):
        """Update player's last login time"""
        if player_id in self.sheets.get_all_players():
            self.sheets.upsert_player({
                'player_id': player_id,
                'name': self.sheets.get_player(player_id)['name'],
                'level': self.sheets.get_player(player_id)['level'],
                'xp': self.sheets.get_player(player_id)['xp'],
                'resources': self.sheets.get_player(player_id)['resources'],
                'army': self.sheets.get_player(player_id)['army'],
                'alliance': self.sheets.get_player(player_id)['alliance'],
                'hustlecoins': self.sheets.get_player(player_id)['hustlecoins'],
                'achievements': self.sheets.get_player(player_id)['achievements'],
                'last_active': time.time(),
                'bag': self.sheets.get_player(player_id)['bag']
            })

    def add_experience(self, player_id: str, amount: int):
        """Add experience to player"""
        if player_id in self.sheets.get_all_players():
            player = self.sheets.get_player(player_id)
            self.sheets.upsert_player({
                'player_id': player_id,
                'name': player['name'],
                'level': player['level'],
                'xp': player['xp'] + amount,
                'resources': player['resources'],
                'army': player['army'],
                'alliance': player['alliance'],
                'hustlecoins': player['hustlecoins'],
                'achievements': player['achievements'],
                'last_active': player['last_active'],
                'bag': player['bag']
            })
            # Check for level up
            self._check_level_up(player_id)

    def _check_level_up(self, player_id: str):
        """Check if player should level up"""
        player = self.sheets.get_player(player_id)
        current_level = player['level']
        experience = player['xp']
        
        # Simple level up formula: level * 1000 experience needed
        required_exp = current_level * 1000
        if experience >= required_exp:
            self.sheets.upsert_player({
                'player_id': player_id,
                'name': player['name'],
                'level': current_level + 1,
                'xp': experience - required_exp,
                'resources': player['resources'],
                'army': player['army'],
                'alliance': player['alliance'],
                'hustlecoins': player['hustlecoins'],
                'achievements': player['achievements'],
                'last_active': player['last_active'],
                'bag': player['bag']
            })

    def _is_valid_name(self, name: str) -> bool:
        """Validate player name"""
        # Only letters, numbers, and spaces
        # Length between 3 and 20 characters
        pattern = r'^[a-zA-Z0-9\s]{3,20}$'
        return bool(re.match(pattern, name))

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by level and experience"""
        players = []
        for player in self.get_all_players():
            players.append({
                'id': player['player_id'],
                'name': player['name'],
                'level': player['level'],
                'experience': player['xp']
            })
        # Sort by level (descending) and experience (descending)
        players.sort(key=lambda x: (x['level'], x['experience']), reverse=True)
        return players[:limit]

    def get_hustlecoins(self, player_id: str) -> int:
        """Get the number of HustleCoins a player has"""
        player = self.get_player(player_id)
        return player.get('hustlecoins', 0) if player else 0

    def add_hustlecoins(self, player_id: str, amount: int) -> bool:
        """Add HustleCoins to a player"""
        player = self.get_player(player_id)
        if not player:
            return False
        player['hustlecoins'] = player.get('hustlecoins', 0) + amount
        self.upsert_player(player)
        return True

    def spend_hustlecoins(self, player_id: str, amount: int) -> bool:
        """Spend HustleCoins if the player has enough"""
        player = self.get_player(player_id)
        if not player or player.get('hustlecoins', 0) < amount:
            return False
        player['hustlecoins'] -= amount
        self.upsert_player(player)
        return True 