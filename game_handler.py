"""
Game Handler for SkyHustle 2
Manages game state and coordinates between different systems
"""

from typing import Dict, List, Optional
from modules.alliance_manager import AllianceManager
from modules.combat_manager import CombatManager
from modules.social_manager import SocialManager
from modules.tutorial_manager import TutorialManager
from modules.progression_manager import ProgressionManager
from config.game_config import GAME_SETTINGS
from config.alliance_config import ALLIANCE_SETTINGS
import random
import time

class GameHandler:
    def __init__(self):
        self.tutorial_manager = TutorialManager()
        self.combat_manager = CombatManager()
        self.social_manager = SocialManager()
        self.progression_manager = ProgressionManager()
        self.alliance_manager = AllianceManager()
        self.players: Dict[str, Dict] = {}
        self.game_state: Dict = {
            'day': 1,
            'time': 0,
            'weather': 'clear',
            'events': []
        }

    def create_player(self, player_id: str, name: str) -> Dict:
        """Create a new player"""
        if player_id in self.players:
            return {'success': False, 'message': 'Player already exists!'}
        
        # Create player data
        player = {
            'id': player_id,
            'name': name,
            'level': 1,
            'xp': 0,
            'resources': {
                'gold': GAME_SETTINGS['starting_gold'],
                'wood': GAME_SETTINGS['starting_wood'],
                'stone': GAME_SETTINGS['starting_stone'],
                'food': GAME_SETTINGS['starting_food']
            },
            'inventory': [],
            'skills': [],
            'quests': [],
            'tutorial_progress': 0,
            'created_at': time.time()
        }
        
        self.players[player_id] = player
        
        # Initialize tutorial
        self.tutorial_manager.start_tutorial(player_id)
        
        return {'success': True, 'player': player}

    def get_player(self, player_id: str) -> Optional[Dict]:
        """Get player information"""
        return self.players.get(player_id)

    def update_player(self, player_id: str, updates: Dict) -> Dict:
        """Update player data"""
        if player_id not in self.players:
            return {'success': False, 'message': 'Player not found!'}
        
        player = self.players[player_id]
        for key, value in updates.items():
            if key in player:
                player[key] = value
        
        return {'success': True, 'player': player}

    def add_resources(self, player_id: str, resources: Dict[str, int]) -> Dict:
        """Add resources to player"""
        if player_id not in self.players:
            return {'success': False, 'message': 'Player not found!'}
        
        player = self.players[player_id]
        for resource, amount in resources.items():
            if resource in player['resources']:
                player['resources'][resource] += amount
        
        return {'success': True, 'resources': player['resources']}

    def remove_resources(self, player_id: str, resources: Dict[str, int]) -> Dict:
        """Remove resources from player"""
        if player_id not in self.players:
            return {'success': False, 'message': 'Player not found!'}
        
        player = self.players[player_id]
        for resource, amount in resources.items():
            if resource in player['resources']:
                if player['resources'][resource] < amount:
                    return {'success': False, 'message': f'Not enough {resource}!'}
                player['resources'][resource] -= amount
        
        return {'success': True, 'resources': player['resources']}

    def add_xp(self, player_id: str, amount: int) -> Dict:
        """Add XP to player"""
        if player_id not in self.players:
            return {'success': False, 'message': 'Player not found!'}
        
        player = self.players[player_id]
        player['xp'] += amount
        
        # Check for level up
        self.progression_manager.check_level_up(player_id, player)
        
        return {'success': True, 'xp': player['xp'], 'level': player['level']}

    def get_alliance_info(self, player_id: str) -> Dict:
        """Get player's alliance information"""
        return self.alliance_manager.get_player_alliance(player_id)

    def create_alliance(self, player_id: str, name: str, description: str) -> Dict:
        """Create a new alliance"""
        # Check player level
        player = self.players.get(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found!'}
        
        if player['level'] < ALLIANCE_SETTINGS['min_level_to_create']:
            return {'success': False, 'message': f'Must be level {ALLIANCE_SETTINGS["min_level_to_create"]} to create an alliance!'}
        
        # Check resources
        if not self._has_resources(player_id, ALLIANCE_SETTINGS['creation_cost']):
            return {'success': False, 'message': 'Not enough resources to create alliance!'}
        
        # Remove resources
        self.remove_resources(player_id, ALLIANCE_SETTINGS['creation_cost'])
        
        # Create alliance
        return self.alliance_manager.create_alliance(player_id, name, description)

    def join_alliance(self, player_id: str, alliance_id: str) -> Dict:
        """Join an alliance"""
        return self.alliance_manager.join_alliance(player_id, alliance_id)

    def leave_alliance(self, player_id: str) -> Dict:
        """Leave current alliance"""
        return self.alliance_manager.leave_alliance(player_id)

    def donate_resources(self, player_id: str, alliance_id: str, resources: Dict[str, int]) -> Dict:
        """Donate resources to alliance"""
        # Check if player has resources
        if not self._has_resources(player_id, resources):
            return {'success': False, 'message': 'Not enough resources!'}
        
        # Remove resources from player
        self.remove_resources(player_id, resources)
        
        # Add resources to alliance
        return self.alliance_manager.donate_resources(player_id, alliance_id, resources)

    def get_alliance_rankings(self) -> List[Dict]:
        """Get alliance rankings"""
        return self.alliance_manager.get_alliance_rankings()

    def add_alliance_chat(self, player_id: str, alliance_id: str, message: str) -> Dict:
        """Add message to alliance chat"""
        return self.alliance_manager.add_chat_message(alliance_id, player_id, message)

    def get_alliance_chat(self, alliance_id: str) -> List[Dict]:
        """Get alliance chat history"""
        return self.alliance_manager.get_chat_history(alliance_id)

    def declare_war(self, player_id: str, target_alliance_id: str) -> Dict:
        """Declare war on another alliance"""
        return self.alliance_manager.declare_war(
            self.alliance_manager.get_player_alliance(player_id)['alliance']['id'],
            target_alliance_id,
            player_id
        )

    def _has_resources(self, player_id: str, resources: Dict[str, int]) -> bool:
        """Check if player has enough resources"""
        player = self.players.get(player_id)
        if not player:
            return False
        
        for resource, amount in resources.items():
            if resource not in player['resources'] or player['resources'][resource] < amount:
                return False
        
        return True

    def update_game_state(self) -> Dict:
        """Update game state (day/night cycle, weather, etc.)"""
        self.game_state['time'] = (self.game_state['time'] + 1) % 24
        if self.game_state['time'] == 0:
            self.game_state['day'] += 1
        
        # Update weather randomly
        if random.random() < 0.1:  # 10% chance to change weather
            self.game_state['weather'] = random.choice(['clear', 'rainy', 'stormy', 'foggy'])
        
        return self.game_state

    def get_game_state(self) -> Dict:
        """Get current game state"""
        return self.game_state 