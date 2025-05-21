"""
Building management module for SkyHustle 2
Handles building construction, upgrades, and effects
"""

import time
from typing import Dict, List, Optional, Tuple
from config.game_config import BUILDINGS

class BuildingManager:
    def __init__(self):
        # Store buildings per player: player_id -> {building_id -> level}
        self.buildings: Dict[str, Dict[str, int]] = {}
        self.upgrade_queue: Dict[str, List[Dict]] = {}  # player_id -> list of upgrades
        self.last_update = time.time()

    def build_building(self, player_id: str, building_id: str, level: int = 1):
        """Construct a building for a player at a given level."""
        if player_id not in self.buildings:
            self.buildings[player_id] = {}
        self.buildings[player_id][building_id] = level

    def get_building_level(self, player_id: str, building_id: str) -> int:
        """Get current level of a building for a player"""
        return self.buildings.get(player_id, {}).get(building_id, 0)

    def get_building_info(self, player_id: str, building_id: str) -> Optional[Dict]:
        """Get information about a building for a player"""
        if building_id not in BUILDINGS:
            return None
        level = self.get_building_level(player_id, building_id)
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

    def can_upgrade(self, player_id: str, building_id: str) -> bool:
        """Check if a building can be upgraded for a player"""
        if building_id not in BUILDINGS:
            return False
        current_level = self.get_building_level(player_id, building_id)
        return current_level < BUILDINGS[building_id]['max_level']

    def queue_upgrade(self, player_id: str, building_id: str) -> Tuple[bool, str]:
        """Queue a building for upgrade for a player"""
        if not self.can_upgrade(player_id, building_id):
            return False, "Building cannot be upgraded further"
        current_level = self.get_building_level(player_id, building_id)
        upgrade_info = {
            'building_id': building_id,
            'from_level': current_level,
            'to_level': current_level + 1,
            'start_time': time.time(),
            'end_time': time.time() + self.get_upgrade_time(building_id, current_level)
        }
        if player_id not in self.upgrade_queue:
            self.upgrade_queue[player_id] = []
        self.upgrade_queue[player_id].append(upgrade_info)
        return True, "Upgrade queued successfully"

    def update_upgrades(self):
        """Update building upgrades and return completed upgrades for all players"""
        current_time = time.time()
        completed = []
        for player_id, queue in self.upgrade_queue.items():
            remaining = []
            for upgrade in queue:
                if current_time >= upgrade['end_time']:
                    # Complete the upgrade
                    self.buildings.setdefault(player_id, {})[upgrade['building_id']] = upgrade['to_level']
                    completed.append({'player_id': player_id, **upgrade})
                else:
                    remaining.append(upgrade)
            self.upgrade_queue[player_id] = remaining
        return completed

    def get_upgrade_queue(self, player_id: str) -> List[Dict]:
        """Get current upgrade queue for a player"""
        return self.upgrade_queue.get(player_id, [])

    def cancel_upgrade(self, player_id: str, building_id: str) -> bool:
        """Cancel a queued upgrade for a player"""
        queue = self.upgrade_queue.get(player_id, [])
        for i, upgrade in enumerate(queue):
            if upgrade['building_id'] == building_id:
                queue.pop(i)
                return True
        return False

    def get_all_buildings(self, player_id: str) -> Dict[str, Dict]:
        """Get information about all buildings for a player"""
        return {
            building_id: {
                'level': self.get_building_level(player_id, building_id),
                'info': BUILDINGS[building_id]
            }
            for building_id in BUILDINGS.keys()
        }

    def get_building_production(self, player_id: str, building_id: str) -> Dict[str, float]:
        """Get current production rates for a building for a player"""
        if building_id not in BUILDINGS or 'production' not in BUILDINGS[building_id]:
            return {}
        level = self.get_building_level(player_id, building_id)
        base_production = BUILDINGS[building_id]['production']
        return {resource: amount * level 
                for resource, amount in base_production.items()} 