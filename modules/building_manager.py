"""
Building management module for SkyHustle 2
Handles building construction, upgrades, and effects (per-player)
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

    def get_buildings(self, player_id: str) -> Dict[str, int]:
        """Get all buildings and their levels for a player"""
        return self.buildings.get(player_id, {})

    def build_building(self, player_id: str, building_id: str, level: int = 1):
        """Construct a building for a player at a given level."""
        if player_id not in self.buildings:
            self.buildings[player_id] = {}
        self.buildings[player_id][building_id] = level

    def get_building_level(self, player_id: str, building_id: str) -> int:
        return self.buildings.get(player_id, {}).get(building_id, 0)

    def get_building_info(self, player_id: str, building_id: str) -> Optional[Dict]:
        if building_id not in BUILDINGS:
            return None
        level = self.get_building_level(player_id, building_id)
        info = BUILDINGS[building_id].copy()
        info['level'] = level
        return info

    def get_upgrade_cost(self, player_id: str, building_id: str) -> Dict[str, int]:
        if building_id not in BUILDINGS:
            return {}
        current_level = self.get_building_level(player_id, building_id)
        base_costs = BUILDINGS[building_id]['base_cost']
        multiplier = 1.5 ** current_level
        return {resource: int(amount * multiplier) for resource, amount in base_costs.items()}

    def get_upgrade_time(self, player_id: str, building_id: str) -> int:
        if building_id not in BUILDINGS:
            return 0
        current_level = self.get_building_level(player_id, building_id)
        base_time = 300  # 5 minutes in seconds
        return int(base_time * (1.3 ** current_level))

    def can_upgrade(self, player_id: str, building_id: str) -> bool:
        if building_id not in BUILDINGS:
            return False
        current_level = self.get_building_level(player_id, building_id)
        return current_level < BUILDINGS[building_id]['max_level']

    def queue_upgrade(self, player_id: str, building_id: str) -> Tuple[bool, str]:
        if not self.can_upgrade(player_id, building_id):
            return False, "Building cannot be upgraded further"
        current_level = self.get_building_level(player_id, building_id)
        upgrade_info = {
            'building_id': building_id,
            'from_level': current_level,
            'to_level': current_level + 1,
            'start_time': time.time(),
            'end_time': time.time() + self.get_upgrade_time(player_id, building_id)
        }
        if player_id not in self.upgrade_queue:
            self.upgrade_queue[player_id] = []
        self.upgrade_queue[player_id].append(upgrade_info)
        return True, "Upgrade queued successfully"

    def update_upgrades(self, player_id: Optional[str] = None) -> List[Dict]:
        current_time = time.time()
        completed = []
        if player_id:
            players = [player_id]
        else:
            players = list(self.upgrade_queue.keys())
        for pid in players:
            remaining = []
            for upgrade in self.upgrade_queue.get(pid, []):
                if current_time >= upgrade['end_time']:
                    self.buildings.setdefault(pid, {})[upgrade['building_id']] = upgrade['to_level']
                    completed.append(upgrade)
                else:
                    remaining.append(upgrade)
            self.upgrade_queue[pid] = remaining
        return completed

    def get_upgrade_queue(self, player_id: str) -> List[Dict]:
        return self.upgrade_queue.get(player_id, [])

    def cancel_upgrade(self, player_id: str, building_id: str) -> bool:
        if player_id not in self.upgrade_queue:
            return False
        for i, upgrade in enumerate(self.upgrade_queue[player_id]):
            if upgrade['building_id'] == building_id:
                self.upgrade_queue[player_id].pop(i)
                return True
        return False

    def get_all_buildings(self, player_id: str) -> Dict[str, Dict]:
        return {
            building_id: {
                'level': self.get_building_level(player_id, building_id),
                'info': BUILDINGS[building_id]
            }
            for building_id in BUILDINGS.keys()
        }

    def get_building_production(self, player_id: str, building_id: str) -> Dict[str, float]:
        if building_id not in BUILDINGS or 'production' not in BUILDINGS[building_id]:
            return {}
        level = self.get_building_level(player_id, building_id)
        base_production = BUILDINGS[building_id]['production']
        return {resource: amount * level for resource, amount in base_production.items()}

    def get_available_buildings(self, player_id: str) -> List[Dict]:
        """Get list of available buildings for a player"""
        available = []
        for building_id, building_info in BUILDINGS.items():
            current_level = self.get_building_level(player_id, building_id)
            if current_level < building_info['max_level']:
                available.append({
                    'id': building_id,
                    'name': building_info['name'],
                    'emoji': building_info['emoji'],
                    'description': building_info['description'],
                    'level': current_level,
                    'max_level': building_info['max_level'],
                    'cost': self.get_upgrade_cost(player_id, building_id)
                })
        return available

    def get_building_requirements(self, building_id: str) -> Dict[str, int]:
        """Get resource requirements for a building"""
        if building_id not in BUILDINGS:
            return {}
        return BUILDINGS[building_id]['base_cost'] 