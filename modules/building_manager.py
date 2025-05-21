"""
Building management module for SkyHustle 2
Handles building construction, upgrades, and effects
"""

import time
from typing import Dict, List, Optional, Tuple
from config.game_config import BUILDINGS

class BuildingManager:
    def __init__(self):
        self.buildings = {}  # building_id -> level
        self.upgrade_queue = []  # List of pending upgrades
        self.last_update = time.time()

    def get_building_level(self, building_id: str) -> int:
        """Get current level of a building"""
        return self.buildings.get(building_id, 0)

    def get_building_info(self, building_id: str) -> Optional[Dict]:
        """Get information about a building"""
        if building_id not in BUILDINGS:
            return None
        
        level = self.get_building_level(building_id)
        info = BUILDINGS[building_id].copy()
        info['level'] = level
        return info

    def get_upgrade_cost(self, building_id: str, current_level: int) -> Dict[str, int]:
        """Calculate cost to upgrade a building to the next level"""
        if building_id not in BUILDINGS:
            return {}
        
        base_costs = BUILDINGS[building_id]['base_cost']
        # Increase costs by 50% per level
        multiplier = 1.5 ** current_level
        return {resource: int(amount * multiplier) 
                for resource, amount in base_costs.items()}

    def get_upgrade_time(self, building_id: str, current_level: int) -> int:
        """Calculate time in seconds to upgrade a building"""
        if building_id not in BUILDINGS:
            return 0
        
        # Base time of 5 minutes, increases by 30% per level
        base_time = 300  # 5 minutes in seconds
        return int(base_time * (1.3 ** current_level))

    def can_upgrade(self, building_id: str) -> bool:
        """Check if a building can be upgraded"""
        if building_id not in BUILDINGS:
            return False
        
        current_level = self.get_building_level(building_id)
        return current_level < BUILDINGS[building_id]['max_level']

    def queue_upgrade(self, building_id: str) -> Tuple[bool, str]:
        """Queue a building for upgrade"""
        if not self.can_upgrade(building_id):
            return False, "Building cannot be upgraded further"
        
        current_level = self.get_building_level(building_id)
        upgrade_info = {
            'building_id': building_id,
            'from_level': current_level,
            'to_level': current_level + 1,
            'start_time': time.time(),
            'end_time': time.time() + self.get_upgrade_time(building_id, current_level)
        }
        
        self.upgrade_queue.append(upgrade_info)
        return True, "Upgrade queued successfully"

    def update_upgrades(self) -> List[Dict]:
        """Update building upgrades and return completed upgrades"""
        current_time = time.time()
        completed = []
        
        # Check for completed upgrades
        remaining = []
        for upgrade in self.upgrade_queue:
            if current_time >= upgrade['end_time']:
                # Complete the upgrade
                self.buildings[upgrade['building_id']] = upgrade['to_level']
                completed.append(upgrade)
            else:
                remaining.append(upgrade)
        
        self.upgrade_queue = remaining
        return completed

    def get_upgrade_queue(self) -> List[Dict]:
        """Get current upgrade queue"""
        return self.upgrade_queue

    def cancel_upgrade(self, building_id: str) -> bool:
        """Cancel a queued upgrade"""
        for i, upgrade in enumerate(self.upgrade_queue):
            if upgrade['building_id'] == building_id:
                self.upgrade_queue.pop(i)
                return True
        return False

    def get_all_buildings(self, player_id: str) -> Dict[str, Dict]:
        """Get information about all buildings"""
        return {
            building_id: {
                'level': self.get_building_level(building_id),
                'info': BUILDINGS[building_id]
            }
            for building_id in BUILDINGS.keys()
        }

    def get_building_production(self, building_id: str) -> Dict[str, float]:
        """Get current production rates for a building"""
        if building_id not in BUILDINGS or 'production' not in BUILDINGS[building_id]:
            return {}
        
        level = self.get_building_level(building_id)
        base_production = BUILDINGS[building_id]['production']
        return {resource: amount * level 
                for resource, amount in base_production.items()} 