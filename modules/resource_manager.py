"""
Resource management module for SkyHustle 2
Handles resource production, consumption, and storage
"""

import time
from typing import Dict, Optional
from config.game_config import RESOURCES, BUILDINGS

class ResourceManager:
    def __init__(self):
        # Store resources per player: player_id -> {resource: amount}
        self.resources: Dict[str, Dict[str, float]] = {}
        self.last_update: Dict[str, float] = {}
        self.buildings: Dict[str, Dict[str, int]] = {}  # player_id -> {building_id: level}
        self.research_effects: Dict[str, Dict[str, float]] = {}  # player_id -> {effect_id: multiplier}

    def update_resources(self, player_id: str) -> Dict[str, float]:
        """Update resources for a player based on time passed and production rates"""
        if player_id not in self.resources:
            self.resources[player_id] = {resource: 0 for resource in RESOURCES.keys()}
        if player_id not in self.last_update:
            self.last_update[player_id] = time.time()
        current_time = time.time()
        time_passed = (current_time - self.last_update[player_id]) / 60  # Convert to minutes
        self.last_update[player_id] = current_time

        # Calculate production for each resource
        for resource in RESOURCES.keys():
            base_production = RESOURCES[resource]['base_production']
            building_bonus = self._calculate_building_bonus(player_id, resource)
            research_bonus = self._calculate_research_bonus(player_id, resource)
            total_production = base_production * building_bonus * research_bonus * time_passed
            self.resources[player_id][resource] += total_production

        return self.resources[player_id]

    def _calculate_building_bonus(self, player_id: str, resource: str) -> float:
        """Calculate production bonus from buildings for a player"""
        bonus = 1.0
        player_buildings = self.buildings.get(player_id, {})
        for building_id, level in player_buildings.items():
            if building_id in BUILDINGS and 'production' in BUILDINGS[building_id]:
                if resource in BUILDINGS[building_id]['production']:
                    base_production = BUILDINGS[building_id]['production'][resource]
                    bonus += (base_production * level) / 100
        return bonus

    def _calculate_research_bonus(self, player_id: str, resource: str) -> float:
        """Calculate production bonus from research for a player"""
        return self.research_effects.get(player_id, {}).get(f"{resource}_production", 1.0)

    def can_afford(self, player_id: str, costs: Dict[str, int]) -> bool:
        """Check if player can afford the given costs"""
        if player_id not in self.resources:
            return False
        return all(self.resources[player_id].get(resource, 0) >= amount 
                  for resource, amount in costs.items())

    def spend_resources(self, player_id: str, costs: Dict[str, int]) -> bool:
        """Spend resources if possible, return True if successful"""
        if not self.can_afford(player_id, costs):
            return False
        for resource, amount in costs.items():
            self.resources[player_id][resource] -= amount
        return True

    def add_resources(self, player_id: str, resources: Dict[str, int]):
        """Add resources to the player's stockpile"""
        if player_id not in self.resources:
            self.resources[player_id] = {resource: 0 for resource in RESOURCES.keys()}
        for resource, amount in resources.items():
            self.resources[player_id][resource] = self.resources[player_id].get(resource, 0) + amount

    def get_resource_amount(self, player_id: str, resource: str) -> float:
        """Get current amount of a specific resource for a player"""
        return self.resources.get(player_id, {}).get(resource, 0)

    def set_building_level(self, player_id: str, building_id: str, level: int):
        """Set the level of a building for a player"""
        if player_id not in self.buildings:
            self.buildings[player_id] = {}
        self.buildings[player_id][building_id] = level

    def set_research_effect(self, player_id: str, effect_id: str, multiplier: float):
        """Set a research effect multiplier for a player"""
        if player_id not in self.research_effects:
            self.research_effects[player_id] = {}
        self.research_effects[player_id][effect_id] = multiplier

    def get_production_rates(self, player_id: str) -> Dict[str, float]:
        """Get current production rates per minute for all resources for a player"""
        rates = {}
        for resource in RESOURCES.keys():
            base_production = RESOURCES[resource]['base_production']
            building_bonus = self._calculate_building_bonus(player_id, resource)
            research_bonus = self._calculate_research_bonus(player_id, resource)
            rates[resource] = base_production * building_bonus * research_bonus
        return rates 