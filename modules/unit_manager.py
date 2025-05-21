"""
Unit Manager Module
Handles unit training, management, and combat
"""

import time
from typing import Dict, Optional
from config.game_config import UNITS

class UnitManager:
    def __init__(self):
        self.units = {}  # Current unit counts
        self.training_queue = {}  # Units being trained
        self.last_update = time.time()
        
        # Initialize units
        for unit_id, unit in UNITS.items():
            self.units[unit_id] = {
                'count': 0,
                'info': unit
            }
    
    def get_all_units(self, player_id: str) -> Dict:
        """Get all unit information"""
        return self.units
    
    def get_unit_info(self, unit_id: str) -> Dict:
        """Get information about a specific unit"""
        return self.units[unit_id]['info']
    
    def get_unit_count(self, unit_id: str) -> int:
        """Get the current count of a unit"""
        return self.units[unit_id]['count']
    
    def get_training_queue(self) -> Dict:
        """Get the current training queue"""
        return self.training_queue
    
    def get_training_cost(self, unit_id: str) -> Dict:
        """Calculate the cost to train a unit"""
        unit = self.units[unit_id]['info']
        return unit['base_cost']
    
    def get_training_time(self, unit_id: str) -> int:
        """Get the time required to train a unit"""
        unit = self.units[unit_id]['info']
        return unit['training_time']
    
    def can_train(self, unit_id: str) -> bool:
        """Check if a unit can be trained"""
        # Check if we have enough population space
        # This could be based on housing buildings or other factors
        return True  # Placeholder
    
    def queue_training(self, unit_id: str) -> bool:
        """Queue a unit for training"""
        if not self.can_train(unit_id):
            return False
        
        # Add to training queue
        if unit_id in self.training_queue:
            self.training_queue[unit_id] += 1
        else:
            self.training_queue[unit_id] = 1
        
        return True
    
    def update_training(self) -> None:
        """Update training progress"""
        current_time = time.time()
        time_passed = current_time - self.last_update
        self.last_update = current_time
        
        # Process training queue
        completed = []
        for unit_id, count in self.training_queue.items():
            training_time = self.get_training_time(unit_id)
            if time_passed >= training_time:
                # Unit training completed
                self.units[unit_id]['count'] += count
                completed.append(unit_id)
        
        # Remove completed units from queue
        for unit_id in completed:
            del self.training_queue[unit_id]
    
    def get_army_strength(self) -> Dict:
        """Calculate total army strength"""
        total_attack = 0
        total_defense = 0
        total_hp = 0
        
        for unit_id, unit in self.units.items():
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
    
    def get_army_size(self) -> int:
        """Get total number of units"""
        return sum(unit['count'] for unit in self.units.values())
    
    def get_army_composition(self) -> Dict:
        """Get detailed army composition"""
        composition = {}
        for unit_id, unit in self.units.items():
            if unit['count'] > 0:
                composition[unit_id] = {
                    'name': unit['info']['name'],
                    'emoji': unit['info']['emoji'],
                    'count': unit['count'],
                    'stats': unit['info']['stats']
                }
        return composition 