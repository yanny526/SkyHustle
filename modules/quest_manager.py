"""
Quest Manager Module
Handles quest generation, tracking, and rewards
"""

import time
from typing import Dict, List, Optional
from config.game_config import QUEST_SETTINGS, QUEST_TYPES, QUEST_REWARDS

class QuestManager:
    def __init__(self):
        self.active_quests = {}  # Store active quests for each player
        self.completed_quests = {}  # Store completed quests for each player
        self.quest_history = {}  # Store quest history for each player
        self.last_quest_refresh = {}  # Track last quest refresh time for each player

    def generate_quests(self, player_id: str) -> Dict:
        """Generate new quests for a player"""
        if player_id not in self.active_quests:
            self.active_quests[player_id] = []
            self.completed_quests[player_id] = []
            self.quest_history[player_id] = []
            self.last_quest_refresh[player_id] = time.time()

        # Check if it's time to refresh quests
        current_time = time.time()
        if current_time - self.last_quest_refresh[player_id] < QUEST_SETTINGS['refresh_cooldown']:
            return {'success': False, 'message': 'Quests refresh in cooldown'}

        # Clear old quests
        self.active_quests[player_id] = []

        # Generate new quests
        for _ in range(QUEST_SETTINGS['quests_per_refresh']):
            quest = self._generate_random_quest()
            self.active_quests[player_id].append(quest)

        self.last_quest_refresh[player_id] = current_time
        return {'success': True, 'quests': self.active_quests[player_id]}

    def _generate_random_quest(self) -> Dict:
        """Generate a random quest"""
        import random
        
        # Select random quest type
        quest_type = random.choice(list(QUEST_TYPES.keys()))
        quest_info = QUEST_TYPES[quest_type]
        
        # Generate random target amount
        min_target = quest_info['min_target']
        max_target = quest_info['max_target']
        target = random.randint(min_target, max_target)
        
        # Generate quest ID
        quest_id = f"quest_{int(time.time())}_{random.randint(1000, 9999)}"
        
        return {
            'id': quest_id,
            'type': quest_type,
            'name': quest_info['name'],
            'description': quest_info['description'].format(target=target),
            'target': target,
            'progress': 0,
            'reward': self._calculate_reward(quest_type, target),
            'created_at': time.time(),
            'expires_at': time.time() + QUEST_SETTINGS['quest_duration']
        }

    def _calculate_reward(self, quest_type: str, target: int) -> Dict:
        """Calculate quest rewards based on type and target"""
        base_reward = QUEST_REWARDS[quest_type]
        reward = {}
        
        # Scale rewards based on target amount
        for resource, amount in base_reward.items():
            reward[resource] = int(amount * (target / 100))  # Scale based on target
        
        return reward

    def update_quest_progress(self, player_id: str, quest_type: str, amount: int) -> Dict:
        """Update progress for quests of a specific type"""
        if player_id not in self.active_quests:
            return {'success': False, 'message': 'No active quests'}

        updated_quests = []
        completed_quests = []

        for quest in self.active_quests[player_id]:
            if quest['type'] == quest_type and quest['progress'] < quest['target']:
                quest['progress'] += amount
                
                # Check if quest is completed
                if quest['progress'] >= quest['target']:
                    quest['progress'] = quest['target']  # Cap at target
                    completed_quests.append(quest)
                else:
                    updated_quests.append(quest)
            else:
                updated_quests.append(quest)

        # Update active quests
        self.active_quests[player_id] = updated_quests

        # Process completed quests
        for quest in completed_quests:
            self.completed_quests[player_id].append(quest)
            self.quest_history[player_id].append({
                'quest': quest,
                'completed_at': time.time()
            })

        return {
            'success': True,
            'updated_quests': updated_quests,
            'completed_quests': completed_quests
        }

    def get_player_quests(self, player_id: str) -> Dict:
        """Get all quests for a player"""
        if player_id not in self.active_quests:
            return {'success': False, 'message': 'No quests found'}

        return {
            'success': True,
            'active_quests': self.active_quests[player_id],
            'completed_quests': self.completed_quests[player_id]
        }

    def get_quest_history(self, player_id: str, limit: int = 10) -> Dict:
        """Get quest history for a player"""
        if player_id not in self.quest_history:
            return {'success': False, 'message': 'No quest history found'}

        history = sorted(
            self.quest_history[player_id],
            key=lambda x: x['completed_at'],
            reverse=True
        )[:limit]

        return {'success': True, 'history': history}

    def check_quest_expiration(self):
        """Check and remove expired quests"""
        current_time = time.time()
        
        for player_id in self.active_quests:
            expired_quests = []
            active_quests = []
            
            for quest in self.active_quests[player_id]:
                if current_time >= quest['expires_at']:
                    expired_quests.append(quest)
                else:
                    active_quests.append(quest)
            
            # Update active quests
            self.active_quests[player_id] = active_quests
            
            # Add expired quests to history
            for quest in expired_quests:
                self.quest_history[player_id].append({
                    'quest': quest,
                    'completed_at': current_time,
                    'status': 'expired'
                }) 