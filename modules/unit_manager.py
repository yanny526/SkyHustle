"""
Unit Manager Module
Handles unit training, management, and combat (per-player)
"""

import time
from typing import Dict, Optional, List
from config.game_config import UNITS

class UnitManager:
    def __init__(self):
        # Store units per player: player_id -> unit_id -> unit info
        self.units: Dict[str, Dict[str, Dict]] = {}
        self.training_queue: Dict[str, Dict[str, int]] = {}  # player_id -> unit_id -> count
        self.last_update: Dict[str, float] = {}

    def train_units(self, player_id: str, unit_id: str, count: int = 1):
        """Train a number of units for a player."""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        if unit_id not in self.units[player_id]:
            self.units[player_id][unit_id] = {'count': 0, 'info': UNITS[unit_id]}
        self.units[player_id][unit_id]['count'] += count

    def get_all_units(self, player_id: str) -> Dict:
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        return self.units[player_id]

    def get_unit_info(self, player_id: str, unit_id: str) -> Dict:
        return self.units.get(player_id, {}).get(unit_id, {}).get('info', {})

    def get_unit_count(self, player_id: str, unit_id: str) -> int:
        return self.units.get(player_id, {}).get(unit_id, {}).get('count', 0)

    def get_training_queue(self, player_id: str) -> Dict[str, int]:
        return self.training_queue.get(player_id, {})

    def queue_training(self, player_id: str, unit_id: str, count: int = 1) -> bool:
        if player_id not in self.training_queue:
            self.training_queue[player_id] = {}
        self.training_queue[player_id][unit_id] = self.training_queue[player_id].get(unit_id, 0) + count
        return True

    def update_training(self, player_id: Optional[str] = None) -> None:
        current_time = time.time()
        if player_id:
            players = [player_id]
        else:
            players = list(self.training_queue.keys())
        for pid in players:
            completed = []
            for unit_id, count in self.training_queue.get(pid, {}).items():
                training_time = self.get_training_time(unit_id)
                # For simplicity, assume all training completes instantly
                self.train_units(pid, unit_id, count)
                completed.append(unit_id)
            for unit_id in completed:
                del self.training_queue[pid][unit_id]

    def get_training_cost(self, unit_id: str) -> Dict:
        return UNITS[unit_id]['base_cost']

    def get_training_time(self, unit_id: str) -> int:
        return UNITS[unit_id]['training_time']

    def get_army_strength(self, player_id: str) -> Dict:
        total_attack = 0
        total_defense = 0
        total_hp = 0
        for unit_id, unit in self.units.get(player_id, {}).items():
            count = unit['count']
            stats = unit['info']['stats']
            total_attack += count * stats['attack']
            total_defense += count * stats['defense']
            total_hp += count * stats['hp']
        return {'attack': total_attack, 'defense': total_defense, 'hp': total_hp}

    def get_army_size(self, player_id: str) -> int:
        return sum(unit['count'] for unit in self.units.get(player_id, {}).values())

    def get_army_composition(self, player_id: str) -> Dict:
        composition = {}
        for unit_id, unit in self.units.get(player_id, {}).items():
            if unit['count'] > 0:
                composition[unit_id] = {
                    'name': unit['info']['name'],
                    'emoji': unit['info']['emoji'],
                    'count': unit['count'],
                    'stats': unit['info']['stats']
                }
        return composition

    def get_available_units(self, player_id: str) -> List[Dict]:
        """Get list of available units for a player"""
        available = []
        for unit_id, unit_info in UNITS.items():
            available.append({
                'id': unit_id,
                'name': unit_info['name'],
                'emoji': unit_info['emoji'],
                'description': unit_info['description'],
                'count': self.get_unit_count(player_id, unit_id),
                'cost': unit_info['base_cost'],
                'stats': unit_info['stats'],
                'training_time': unit_info['training_time']
            })
        return available

    def get_army(self, player_id: str) -> Dict[str, int]:
        """Get all units and their counts for a player"""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        return {unit_id: unit['count'] for unit_id, unit in self.units[player_id].items() if unit['count'] > 0} 