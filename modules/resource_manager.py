"""
Resource management module for SkyHustle 2
Handles resource production, consumption, and storage
"""

import time
from typing import Dict, Optional
from config.game_config import RESOURCES, BUILDINGS

class ResourceManager:
    def __init__(self):
        self.resources = {resource: 0 for resource in RESOURCES.keys()}
        self.last_update = time.time()
        self.buildings = {}  # Will store building levels
        self.research_effects = {}  # Will store research multipliers

    def update_resources(self) -> Dict[str, int]:
        """Update resources based on time passed and production rates"""
        current_time = time.time()
        time_passed = (current_time - self.last_update) / 60  # Convert to minutes
        self.last_update = current_time

        # Calculate production for each resource
        for resource in RESOURCES.keys():
            base_production = RESOURCES[resource]['base_production']
            building_bonus = self._calculate_building_bonus(resource)
            research_bonus = self._calculate_research_bonus(resource)
            
            total_production = base_production * building_bonus * research_bonus * time_passed
            self.resources[resource] += total_production

        return self.resources

    def _calculate_building_bonus(self, resource: str) -> float:
        """Calculate production bonus from buildings"""
        bonus = 1.0
        for building_id, level in self.buildings.items():
            if building_id in BUILDINGS and 'production' in BUILDINGS[building_id]:
                if resource in BUILDINGS[building_id]['production']:
                    base_production = BUILDINGS[building_id]['production'][resource]
                    bonus += (base_production * level) / 100
        return bonus

    def _calculate_research_bonus(self, resource: str) -> float:
        """Calculate production bonus from research"""
        return self.research_effects.get(f"{resource}_production", 1.0)

    def can_afford(self, costs: Dict[str, int]) -> bool:
        """Check if player can afford the given costs"""
        return all(self.resources.get(resource, 0) >= amount 
                  for resource, amount in costs.items())

    def spend_resources(self, costs: Dict[str, int]) -> bool:
        """Spend resources if possible, return True if successful"""
        if not self.can_afford(costs):
            return False
        
        for resource, amount in costs.items():
            self.resources[resource] -= amount
        return True

    def add_resources(self, resources: Dict[str, int]):
        """Add resources to the player's stockpile"""
        for resource, amount in resources.items():
            self.resources[resource] = self.resources.get(resource, 0) + amount

    def get_resource_amount(self, resource: str) -> int:
        """Get current amount of a specific resource"""
        return self.resources.get(resource, 0)

    def set_building_level(self, building_id: str, level: int):
        """Set the level of a building"""
        self.buildings[building_id] = level

    def set_research_effect(self, effect_id: str, multiplier: float):
        """Set a research effect multiplier"""
        self.research_effects[effect_id] = multiplier

    def get_production_rates(self) -> Dict[str, float]:
        """Get current production rates per minute for all resources"""
        rates = {}
        for resource in RESOURCES.keys():
            base_production = RESOURCES[resource]['base_production']
            building_bonus = self._calculate_building_bonus(resource)
            research_bonus = self._calculate_research_bonus(resource)
            rates[resource] = base_production * building_bonus * research_bonus
        return rates 