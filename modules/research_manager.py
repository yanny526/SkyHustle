"""
Research Manager Module
Handles research, technology upgrades, and bonuses
"""

import time
from typing import Dict, Optional
from config.game_config import RESEARCH

class ResearchManager:
    def __init__(self):
        # Store research per player: player_id -> category -> research dict
        self.research: Dict[str, Dict[str, Dict]] = {}
        self.research_queue: Dict[str, Dict[str, float]] = {}  # player_id -> research_id -> time left
        self.last_update: Dict[str, float] = {}

    def _init_player(self, player_id: str):
        if player_id not in self.research:
            self.research[player_id] = {}
            for category, items in RESEARCH.items():
                self.research[player_id][category] = {}
                for research_id, item in items.items():
                    self.research[player_id][category][research_id] = {
                        'level': 0,
                        'info': item
                    }
        if player_id not in self.research_queue:
            self.research_queue[player_id] = {}
        if player_id not in self.last_update:
            self.last_update[player_id] = time.time()

    def get_all_research(self, player_id: str) -> Dict:
        """Get all research information for a player"""
        self._init_player(player_id)
        return self.research[player_id]
    
    def get_research_info(self, player_id: str, research_id: str) -> Dict:
        """Get information about a specific research for a player"""
        self._init_player(player_id)
        for category in self.research[player_id].values():
            if research_id in category:
                return category[research_id]['info']
        return None
    
    def get_research_level(self, player_id: str, research_id: str) -> int:
        """Get the current level of a research for a player"""
        self._init_player(player_id)
        for category in self.research[player_id].values():
            if research_id in category:
                return category[research_id]['level']
        return 0
    
    def get_research_queue(self, player_id: str) -> Dict:
        """Get the current research queue for a player"""
        self._init_player(player_id)
        return self.research_queue[player_id]
    
    def get_research_cost(self, player_id: str, research_id: str) -> Dict:
        """Calculate the cost to research a technology for a player"""
        info = self.get_research_info(player_id, research_id)
        level = self.get_research_level(player_id, research_id)
        
        # Increase cost by 50% per level
        cost_multiplier = 1.5 ** level
        return {
            resource: int(amount * cost_multiplier)
            for resource, amount in info['base_cost'].items()
        }
    
    def get_research_time(self, player_id: str, research_id: str) -> int:
        """Get the time required to research a technology for a player"""
        info = self.get_research_info(player_id, research_id)
        level = self.get_research_level(player_id, research_id)
        
        # Increase time by 30% per level
        time_multiplier = 1.3 ** level
        return int(info['research_time'] * time_multiplier)
    
    def can_research(self, player_id: str, research_id: str) -> bool:
        """Check if a research can be started for a player"""
        info = self.get_research_info(player_id, research_id)
        level = self.get_research_level(player_id, research_id)
        
        # Check if max level reached
        if level >= info['max_level']:
            return False
        
        # Check if prerequisites are met
        if 'prerequisites' in info:
            for prereq_id, prereq_level in info['prerequisites'].items():
                if self.get_research_level(player_id, prereq_id) < prereq_level:
                    return False
        
        return True
    
    def queue_research(self, player_id: str, research_id: str) -> bool:
        """Queue a research project for a player"""
        self._init_player(player_id)
        if not self.can_research(player_id, research_id):
            return False
        
        # Add to research queue
        self.research_queue[player_id][research_id] = self.get_research_time(player_id, research_id)
        return True
    
    def update_research(self):
        """Update research progress for all players"""
        current_time = time.time()
        for player_id, queue in self.research_queue.items():
            if player_id not in self.last_update:
                self.last_update[player_id] = current_time
            time_passed = current_time - self.last_update[player_id]
            self.last_update[player_id] = current_time
            
            # Process research queue
            completed = []
            for research_id, time_left in queue.items():
                if time_passed >= time_left:
                    # Research completed
                    for category in self.research[player_id].values():
                        if research_id in category:
                            category[research_id]['level'] += 1
                            completed.append(research_id)
                            break
                else:
                    queue[research_id] -= time_passed
            
            # Remove completed research from queue
            for research_id in completed:
                del queue[research_id]
    
    def get_all_bonuses(self, player_id: str) -> Dict:
        """Get all active research bonuses for a player"""
        self._init_player(player_id)
        bonuses = {}
        
        for category, items in self.research[player_id].items():
            bonuses[category] = {}
            for research_id, item in items.items():
                level = item['level']
                if level > 0:
                    info = item['info']
                    # Calculate bonus based on level
                    bonus = info['effect'] * level
                    bonuses[category][research_id] = bonus
        
        return bonuses
    
    def get_category_bonus(self, player_id: str, category: str) -> float:
        """Get total bonus for a specific category for a player"""
        bonuses = self.get_all_bonuses(player_id)
        if category not in bonuses:
            return 0.0
        
        return sum(bonuses[category].values())
    
    def get_research_bonus(self, player_id: str, research_id: str) -> float:
        """Get bonus from a specific research for a player"""
        level = self.get_research_level(player_id, research_id)
        if level == 0:
            return 0.0
        
        info = self.get_research_info(player_id, research_id)
        return info['effect'] * level 