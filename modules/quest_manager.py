"""
Quest Manager Module
Handles quests, progress, and rewards (per-player)
"""

import time
from typing import Dict, List, Optional
from config.game_config import QUESTS

class QuestManager:
    def __init__(self):
        # Store quests per player: player_id -> quest state
        self.active_quests: Dict[str, List[Dict]] = {}
        self.completed_quests: Dict[str, List[Dict]] = {}
        self.quest_history: Dict[str, List[Dict]] = {}
        self.last_quest_refresh: Dict[str, float] = {}

    def get_player_quests(self, player_id: str) -> Dict:
        if player_id not in self.active_quests:
            self.active_quests[player_id] = []
        if player_id not in self.completed_quests:
            self.completed_quests[player_id] = []
        return {
            'success': True,
            'active_quests': self.active_quests[player_id],
            'completed_quests': self.completed_quests[player_id]
        }

    def add_quest(self, player_id: str, quest_id: str) -> bool:
        if player_id not in self.active_quests:
            self.active_quests[player_id] = []
        quest = QUESTS.get(quest_id)
        if not quest:
            return False
        self.active_quests[player_id].append({
            'id': quest_id,
            'name': quest['name'],
            'description': quest['description'],
            'progress': 0,
            'target': quest['target'],
            'reward': quest['reward']
        })
        return True

    def complete_quest(self, player_id: str, quest_id: str) -> bool:
        if player_id not in self.active_quests:
            return False
        quest = next((q for q in self.active_quests[player_id] if q['id'] == quest_id), None)
        if not quest:
            return False
        self.active_quests[player_id].remove(quest)
        if player_id not in self.completed_quests:
            self.completed_quests[player_id] = []
        self.completed_quests[player_id].append(quest)
        return True

    def check_quest_expiration(self):
        # Placeholder for quest expiration logic
        pass 