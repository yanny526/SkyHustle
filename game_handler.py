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
from config.alliance_config import ALLIANCE_SETTINGS
from config.game_config import GAME_SETTINGS
import random
import time
from modules.player_manager import PlayerManager

class GameHandler:
    def __init__(self):
        self.tutorial_manager = TutorialManager()
        self.combat_manager = CombatManager()
        self.social_manager = SocialManager()
        self.progression_manager = ProgressionManager()
        self.alliance_manager = AllianceManager()
        self.player_manager = PlayerManager()
        self.game_state: Dict = {
            'day': 1,
            'time': 0,
            'weather': 'clear',
            'events': []
        }

    def create_player(self, player_id: str, name: str) -> Dict:
        """Create a new player"""
        # Use PlayerManager for persistence
        player = self.player_manager.get_player(player_id)
        if player:
            return {'success': False, 'message': 'Player already exists!'}
        result = self.player_manager.create_player(player_id)
        if not result.get('success'):
            return result
        # Set name after creation
        self.player_manager.set_player_name(player_id, name)
        self.tutorial_manager.start_tutorial(player_id)
        return {'success': True, 'player': self.player_manager.get_player(player_id)}

    def get_player(self, player_id: str) -> Optional[Dict]:
        """Get player information"""
        return self.player_manager.get_player(player_id)

    def update_player(self, player_id: str, updates: Dict) -> Dict:
        """Update player data"""
        player = self.player_manager.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found!'}
        player.update(updates)
        self.player_manager.upsert_player(player)
        return {'success': True, 'player': player}

    def add_resources(self, player_id: str, resources: Dict[str, int]) -> Dict:
        """Add resources to player"""
        player = self.player_manager.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found!'}
        for resource, amount in resources.items():
            if resource in player['resources']:
                player['resources'][resource] += amount
        self.player_manager.upsert_player(player)
        return {'success': True, 'resources': player['resources']}

    def remove_resources(self, player_id: str, resources: Dict[str, int]) -> Dict:
        """Remove resources from player"""
        player = self.player_manager.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found!'}
        for resource, amount in resources.items():
            if resource in player['resources']:
                if player['resources'][resource] < amount:
                    return {'success': False, 'message': f'Not enough {resource}!'}
                player['resources'][resource] -= amount
        self.player_manager.upsert_player(player)
        return {'success': True, 'resources': player['resources']}

    def add_xp(self, player_id: str, amount: int) -> Dict:
        """Add XP to player"""
        player = self.player_manager.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found!'}
        player['xp'] += amount
        self.player_manager.upsert_player(player)
        # Check for level up
        self.progression_manager.check_level_up(player_id, player)
        return {'success': True, 'xp': player['xp'], 'level': player['level']}

    def get_alliance_info(self, player_id: str) -> Dict:
        """Get player's alliance information"""
        return self.alliance_manager.get_player_alliance(player_id)

    def create_alliance(self, player_id: str, name: str, description: str) -> Dict:
        """Create a new alliance"""
        player = self.player_manager.get_player(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found!'}
        if player['level'] < ALLIANCE_SETTINGS['min_level_to_create']:
            return {'success': False, 'message': f'Must be level {ALLIANCE_SETTINGS["min_level_to_create"]} to create an alliance!'}
        if not self._has_resources(player_id, ALLIANCE_SETTINGS['creation_cost']):
            return {'success': False, 'message': 'Not enough resources to create alliance!'}
        self.remove_resources(player_id, ALLIANCE_SETTINGS['creation_cost'])
        return self.alliance_manager.create_alliance(player_id, name, description)

    def join_alliance(self, player_id: str, alliance_id: str) -> Dict:
        """Join an alliance"""
        return self.alliance_manager.join_alliance(player_id, alliance_id)

    def leave_alliance(self, player_id: str) -> Dict:
        """Leave current alliance"""
        return self.alliance_manager.leave_alliance(player_id)

    def donate_resources(self, player_id: str, alliance_id: str, resources: Dict[str, int]) -> Dict:
        """Donate resources to alliance"""
        if not self._has_resources(player_id, resources):
            return {'success': False, 'message': 'Not enough resources!'}
        self.remove_resources(player_id, resources)
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
        player_alliance = self.alliance_manager.get_player_alliance(player_id)
        if not player_alliance or 'alliance' not in player_alliance:
            return {'success': False, 'message': 'Player is not in an alliance!'}
        return self.alliance_manager.declare_war(
            player_alliance['alliance']['id'],
            target_alliance_id,
            player_id
        )

    def _has_resources(self, player_id: str, resources: Dict[str, int]) -> bool:
        """Check if player has enough resources"""
        player = self.player_manager.get_player(player_id)
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
        if random.random() < 0.1:  # 10% chance to change weather
            self.game_state['weather'] = random.choice(['clear', 'rainy', 'stormy', 'foggy'])
        return self.game_state

    def get_game_state(self) -> Dict:
        """Get current game state"""
        return self.game_state 