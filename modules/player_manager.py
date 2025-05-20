"""
Player Manager Module
Handles player profiles, names, and data storage
"""

import re
from typing import Dict, Optional, List
import json
import os
import time

class PlayerManager:
    def __init__(self):
        self.players = {}  # Store player data
        self.names = {}    # Store player names
        self._load_data()

    def _load_data(self):
        """Load player data from storage"""
        try:
            if os.path.exists('data/players.json'):
                with open('data/players.json', 'r') as f:
                    data = json.load(f)
                    self.players = data.get('players', {})
                    self.names = data.get('names', {})
        except Exception as e:
            print(f"Error loading player data: {e}")
            self.players = {}
            self.names = {}

    def _save_data(self):
        """Save player data to storage"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/players.json', 'w') as f:
                json.dump({
                    'players': self.players,
                    'names': self.names
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving player data: {e}")

    def create_player(self, player_id: str) -> Dict:
        """Create a new player profile"""
        if player_id in self.players:
            return {'success': False, 'message': 'Player already exists'}

        self.players[player_id] = {
            'created_at': time.time(),
            'last_login': time.time(),
            'level': 1,
            'experience': 0,
            'hustlecoins': 0  # Premium currency
        }
        self._save_data()
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
        if name.lower() in [n.lower() for n in self.names.values()]:
            return {'success': False, 'message': 'This name is already taken'}

        # Set name
        self.names[player_id] = name
        self._save_data()
        return {'success': True}

    def get_player_name(self, player_id: str) -> str:
        """Get player's display name"""
        return self.names.get(player_id, f"Player_{player_id[:8]}")

    def get_player_profile(self, player_id: str) -> Dict:
        """Get player's profile information"""
        if player_id not in self.players:
            return {'success': False, 'message': 'Player not found'}

        return {
            'success': True,
            'name': self.get_player_name(player_id),
            'level': self.players[player_id]['level'],
            'experience': self.players[player_id]['experience'],
            'created_at': self.players[player_id]['created_at'],
            'last_login': self.players[player_id]['last_login']
        }

    def update_last_login(self, player_id: str):
        """Update player's last login time"""
        if player_id in self.players:
            self.players[player_id]['last_login'] = time.time()
            self._save_data()

    def add_experience(self, player_id: str, amount: int):
        """Add experience to player"""
        if player_id in self.players:
            self.players[player_id]['experience'] += amount
            # Check for level up
            self._check_level_up(player_id)
            self._save_data()

    def _check_level_up(self, player_id: str):
        """Check if player should level up"""
        player = self.players[player_id]
        current_level = player['level']
        experience = player['experience']
        
        # Simple level up formula: level * 1000 experience needed
        required_exp = current_level * 1000
        if experience >= required_exp:
            player['level'] += 1
            player['experience'] -= required_exp

    def _is_valid_name(self, name: str) -> bool:
        """Validate player name"""
        # Only letters, numbers, and spaces
        # Length between 3 and 20 characters
        pattern = r'^[a-zA-Z0-9\s]{3,20}$'
        return bool(re.match(pattern, name))

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by level and experience"""
        players = []
        for player_id, data in self.players.items():
            players.append({
                'id': player_id,
                'name': self.get_player_name(player_id),
                'level': data['level'],
                'experience': data['experience']
            })
        
        # Sort by level (descending) and experience (descending)
        players.sort(key=lambda x: (x['level'], x['experience']), reverse=True)
        return players[:limit]

    def get_hustlecoins(self, player_id: str) -> int:
        """Get the number of HustleCoins a player has"""
        return self.players.get(player_id, {}).get('hustlecoins', 0)

    def add_hustlecoins(self, player_id: str, amount: int) -> bool:
        """Add HustleCoins to a player"""
        if player_id not in self.players:
            return False
        self.players[player_id]['hustlecoins'] = self.players[player_id].get('hustlecoins', 0) + amount
        self._save_data()
        return True

    def spend_hustlecoins(self, player_id: str, amount: int) -> bool:
        """Spend HustleCoins if the player has enough"""
        if player_id not in self.players:
            return False
        if self.players[player_id].get('hustlecoins', 0) < amount:
            return False
        self.players[player_id]['hustlecoins'] -= amount
        self._save_data()
        return True 