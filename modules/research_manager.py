"""
Research Manager Module
Handles research, technology upgrades, and bonuses (per-player)
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
        self._init_player(player_id)
        return self.research[player_id]

    def get_research_info(self, player_id: str, research_id: str) -> Optional[Dict]:
        self._init_player(player_id)
        for category in self.research[player_id].values():
            if research_id in category:
                return category[research_id]['info']
        return None

    def get_research_level(self, player_id: str, research_id: str) -> int:
        self._init_player(player_id)
        for category in self.research[player_id].values():
            if research_id in category:
                return category[research_id]['level']
        return 0

    def get_research_queue(self, player_id: str) -> Dict[str, float]:
        self._init_player(player_id)
        return self.research_queue[player_id]

    def get_research_cost(self, player_id: str, research_id: str) -> Dict:
        info = self.get_research_info(player_id, research_id)
        level = self.get_research_level(player_id, research_id)
        cost_multiplier = 1.5 ** level
        return {resource: int(amount * cost_multiplier) for resource, amount in info['base_cost'].items()}

    def get_research_time(self, player_id: str, research_id: str) -> int:
        info = self.get_research_info(player_id, research_id)
        level = self.get_research_level(player_id, research_id)
        time_multiplier = 1.3 ** level
        return int(info['research_time'] * time_multiplier)

    def can_research(self, player_id: str, research_id: str) -> bool:
        info = self.get_research_info(player_id, research_id)
        level = self.get_research_level(player_id, research_id)
        if level >= info['max_level']:
            return False
        if 'prerequisites' in info:
            for prereq_id, prereq_level in info['prerequisites'].items():
                if self.get_research_level(player_id, prereq_id) < prereq_level:
                    return False
        return True

    def queue_research(self, player_id: str, research_id: str) -> bool:
        self._init_player(player_id)
        if not self.can_research(player_id, research_id):
            return False
        self.research_queue[player_id][research_id] = self.get_research_time(player_id, research_id)
        return True

    def update_research(self, player_id: Optional[str] = None) -> None:
        current_time = time.time()
        if player_id:
            players = [player_id]
        else:
            players = list(self.research_queue.keys())
        for pid in players:
            completed = []
            for research_id, time_left in self.research_queue.get(pid, {}).items():
                if time_left <= (current_time - self.last_update.get(pid, current_time)):
                    # Research completed
                    for category in self.research[pid].values():
                        if research_id in category:
                            category[research_id]['level'] += 1
                            completed.append(research_id)
                            break
                else:
                    self.research_queue[pid][research_id] -= (current_time - self.last_update.get(pid, current_time))
            for research_id in completed:
                del self.research_queue[pid][research_id]
            self.last_update[pid] = current_time

    def get_all_bonuses(self, player_id: str) -> Dict:
        self._init_player(player_id)
        bonuses = {}
        for category, items in self.research[player_id].items():
            bonuses[category] = {}
            for research_id, item in items.items():
                level = item['level']
                if level > 0:
                    info = item['info']
                    bonus = info['effect'] * level
                    bonuses[category][research_id] = bonus
        return bonuses

    def get_category_bonus(self, player_id: str, category: str) -> float:
        bonuses = self.get_all_bonuses(player_id)
        if category not in bonuses:
            return 0.0
        return sum(bonuses[category].values())

    def get_research_bonus(self, player_id: str, research_id: str) -> float:
        level = self.get_research_level(player_id, research_id)
        if level == 0:
            return 0.0
        info = self.get_research_info(player_id, research_id)
        return info['effect'] * level 