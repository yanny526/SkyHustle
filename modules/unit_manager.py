"""
Unit Manager Module
Handles unit training, management, and combat
"""

import time
from typing import Dict, Optional
from config.game_config import UNITS

class UnitManager:
    def __init__(self):
        # Store units per player: player_id -> unit_id -> unit info
        self.units: Dict[str, Dict[str, Dict]] = {}
        self.training_queue: Dict[str, Dict[str, int]] = {}  # player_id -> unit_id -> count
        self.last_update: Dict[str, float] = {}
        # No need to initialize units for all players here

    def train_units(self, player_id: str, unit_id: str, count: int = 1):
        """Train a number of units for a player."""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        if unit_id not in self.units[player_id]:
            self.units[player_id][unit_id] = {'count': 0, 'info': UNITS[unit_id]}
        self.units[player_id][unit_id]['count'] += count

    def get_all_units(self, player_id: str) -> Dict:
        """Get all unit information for a player"""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        return self.units[player_id]
    
    def get_unit_info(self, player_id: str, unit_id: str) -> Dict:
        """Get information about a specific unit for a player"""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        return self.units[player_id][unit_id]['info']
    
    def get_unit_count(self, player_id: str, unit_id: str) -> int:
        """Get the current count of a unit for a player"""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        return self.units[player_id][unit_id]['count']
    
    def get_training_queue(self, player_id: str) -> Dict:
        """Get the current training queue for a player"""
        return self.training_queue.get(player_id, {})
    
    def get_training_cost(self, unit_id: str) -> Dict:
        """Calculate the cost to train a unit"""
        return UNITS[unit_id]['base_cost']
    
    def get_training_time(self, unit_id: str) -> int:
        """Get the time required to train a unit"""
        return UNITS[unit_id]['training_time']
    
    def can_train(self, player_id: str, unit_id: str) -> bool:
        """Check if a unit can be trained for a player"""
        # Placeholder: always True
        return True
    
    def queue_training(self, player_id: str, unit_id: str, count: int = 1) -> bool:
        """Queue a unit for training for a player"""
        if not self.can_train(player_id, unit_id):
            return False
        if player_id not in self.training_queue:
            self.training_queue[player_id] = {}
        if unit_id in self.training_queue[player_id]:
            self.training_queue[player_id][unit_id] += count
        else:
            self.training_queue[player_id][unit_id] = count
        return True
    
    def update_training(self):
        """Update training progress for all players"""
        current_time = time.time()
        for player_id, queue in self.training_queue.items():
            if player_id not in self.last_update:
                self.last_update[player_id] = current_time
            time_passed = current_time - self.last_update[player_id]
            self.last_update[player_id] = current_time
            completed = []
            for unit_id, count in queue.items():
                training_time = self.get_training_time(unit_id)
                # For simplicity, assume all units finish if enough time has passed
                if time_passed >= training_time:
                    self.train_units(player_id, unit_id, count)
                    completed.append(unit_id)
            for unit_id in completed:
                del queue[unit_id]
    
    def get_army_strength(self, player_id: str) -> Dict:
        """Calculate total army strength for a player"""
        total_attack = 0
        total_defense = 0
        total_hp = 0
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        for unit_id, unit in self.units[player_id].items():
            count = unit['count']
            stats = unit['info']['stats']
            total_attack += count * stats['attack']
            total_defense += count * stats['defense']
            total_hp += count * stats['hp']
        return {
            'attack': total_attack,
            'defense': total_defense,
            'hp': total_hp
        }
    
    def get_army_size(self, player_id: str) -> int:
        """Get total number of units for a player"""
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        return sum(unit['count'] for unit in self.units[player_id].values())
    
    def get_army_composition(self, player_id: str) -> Dict:
        """Get detailed army composition for a player"""
        composition = {}
        if player_id not in self.units:
            self.units[player_id] = {uid: {'count': 0, 'info': unit} for uid, unit in UNITS.items()}
        for unit_id, unit in self.units[player_id].items():
            if unit['count'] > 0:
                composition[unit_id] = {
                    'name': unit['info']['name'],
                    'emoji': unit['info']['emoji'],
                    'count': unit['count'],
                    'stats': unit['info']['stats']
                }
        return composition 