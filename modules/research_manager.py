"""
Research Manager Module
Handles research, technology upgrades, and bonuses
"""

import time
from typing import Dict, Optional
from config.game_config import RESEARCH

class ResearchManager:
    def __init__(self):
        self.research = {}  # Current research levels
        self.research_queue = {}  # Research in progress
        self.last_update = time.time()
        
        # Initialize research
        for category, items in RESEARCH.items():
            self.research[category] = {}
            for research_id, item in items.items():
                self.research[category][research_id] = {
                    'level': 0,
                    'info': item
                }
    
    def get_all_research(self, player_id: str) -> Dict:
        """Get all research information"""
        return self.research
    
    def get_research_info(self, research_id: str) -> Dict:
        """Get information about a specific research"""
        # Find the research in the correct category
        for category in self.research.values():
            if research_id in category:
                return category[research_id]['info']
        return None
    
    def get_research_level(self, research_id: str) -> int:
        """Get the current level of a research"""
        # Find the research in the correct category
        for category in self.research.values():
            if research_id in category:
                return category[research_id]['level']
        return 0
    
    def get_research_queue(self) -> Dict:
        """Get the current research queue"""
        return self.research_queue
    
    def get_research_cost(self, research_id: str) -> Dict:
        """Calculate the cost to research a technology"""
        info = self.get_research_info(research_id)
        level = self.get_research_level(research_id)
        
        # Increase cost by 50% per level
        cost_multiplier = 1.5 ** level
        return {
            resource: int(amount * cost_multiplier)
            for resource, amount in info['base_cost'].items()
        }
    
    def get_research_time(self, research_id: str) -> int:
        """Get the time required to research a technology"""
        info = self.get_research_info(research_id)
        level = self.get_research_level(research_id)
        
        # Increase time by 30% per level
        time_multiplier = 1.3 ** level
        return int(info['research_time'] * time_multiplier)
    
    def can_research(self, research_id: str) -> bool:
        """Check if a research can be started"""
        info = self.get_research_info(research_id)
        level = self.get_research_level(research_id)
        
        # Check if max level reached
        if level >= info['max_level']:
            return False
        
        # Check if prerequisites are met
        if 'prerequisites' in info:
            for prereq_id, prereq_level in info['prerequisites'].items():
                if self.get_research_level(prereq_id) < prereq_level:
                    return False
        
        return True
    
    def queue_research(self, research_id: str) -> bool:
        """Queue a research project"""
        if not self.can_research(research_id):
            return False
        
        # Add to research queue
        self.research_queue[research_id] = self.get_research_time(research_id)
        return True
    
    def update_research(self) -> None:
        """Update research progress"""
        current_time = time.time()
        time_passed = current_time - self.last_update
        self.last_update = current_time
        
        # Process research queue
        completed = []
        for research_id, time_left in self.research_queue.items():
            if time_passed >= time_left:
                # Research completed
                # Find the research in the correct category
                for category in self.research.values():
                    if research_id in category:
                        category[research_id]['level'] += 1
                        completed.append(research_id)
                        break
            else:
                self.research_queue[research_id] -= time_passed
        
        # Remove completed research from queue
        for research_id in completed:
            del self.research_queue[research_id]
    
    def get_all_bonuses(self) -> Dict:
        """Get all active research bonuses"""
        bonuses = {}
        
        for category, items in self.research.items():
            bonuses[category] = {}
            for research_id, item in items.items():
                level = item['level']
                if level > 0:
                    info = item['info']
                    # Calculate bonus based on level
                    bonus = info['effect'] * level
                    bonuses[category][research_id] = bonus
        
        return bonuses
    
    def get_category_bonus(self, category: str) -> float:
        """Get total bonus for a specific category"""
        bonuses = self.get_all_bonuses()
        if category not in bonuses:
            return 0.0
        
        return sum(bonuses[category].values())
    
    def get_research_bonus(self, research_id: str) -> float:
        """Get bonus from a specific research"""
        level = self.get_research_level(research_id)
        if level == 0:
            return 0.0
        
        info = self.get_research_info(research_id)
        return info['effect'] * level 