"""
Alliance Resource Manager for SkyHustle 2
Handles alliance resource storage, withdrawal, distribution, and protection
"""

import time
from typing import Dict, List, Optional
from config.alliance_config import ALLIANCE_SETTINGS
from config.game_config import RESOURCES

class AllianceResourceManager:
    def __init__(self):
        self.alliance_resources: Dict[str, Dict[str, int]] = {}  # alliance_id -> resources
        self.withdrawal_history: Dict[str, List[Dict]] = {}  # alliance_id -> withdrawal records
        self.distribution_history: Dict[str, List[Dict]] = {}  # alliance_id -> distribution records
        self.protection_status: Dict[str, Dict] = {}  # alliance_id -> protection status

    def initialize_alliance_resources(self, alliance_id: str) -> bool:
        """Initialize resource storage for a new alliance"""
        if alliance_id in self.alliance_resources:
            return False
            
        self.alliance_resources[alliance_id] = {
            'gold': 0,
            'wood': 0,
            'stone': 0,
            'food': 0
        }
        self.withdrawal_history[alliance_id] = []
        self.distribution_history[alliance_id] = []
        self.protection_status[alliance_id] = {
            'is_protected': False,
            'protection_end_time': 0,
            'last_war_time': 0
        }
        return True

    def get_alliance_resources(self, alliance_id: str) -> Dict[str, int]:
        """Get current alliance resources"""
        return self.alliance_resources.get(alliance_id, {})

    def add_resources(self, alliance_id: str, resources: Dict[str, int]) -> bool:
        """Add resources to alliance storage"""
        if alliance_id not in self.alliance_resources:
            return False
            
        for resource, amount in resources.items():
            if resource in self.alliance_resources[alliance_id]:
                self.alliance_resources[alliance_id][resource] += amount
        return True

    def remove_resources(self, alliance_id: str, resources: Dict[str, int]) -> bool:
        """Remove resources from alliance storage"""
        if alliance_id not in self.alliance_resources:
            return False
            
        # Check if alliance has enough resources
        for resource, amount in resources.items():
            if (resource not in self.alliance_resources[alliance_id] or 
                self.alliance_resources[alliance_id][resource] < amount):
                return False
                
        # Remove resources
        for resource, amount in resources.items():
            self.alliance_resources[alliance_id][resource] -= amount
        return True

    def request_withdrawal(self, alliance_id: str, player_id: str, resources: Dict[str, int], reason: str) -> bool:
        """Request resource withdrawal from alliance storage"""
        if alliance_id not in self.alliance_resources:
            return False
            
        # Check if alliance has enough resources
        if not self.remove_resources(alliance_id, resources):
            return False
            
        # Record withdrawal
        self.withdrawal_history[alliance_id].append({
            'player_id': player_id,
            'resources': resources,
            'reason': reason,
            'timestamp': time.time()
        })
        return True

    def distribute_resources(self, alliance_id: str, player_id: str, target_id: str, resources: Dict[str, int], reason: str) -> bool:
        """Distribute resources to alliance members"""
        if alliance_id not in self.alliance_resources:
            return False
            
        # Check if alliance has enough resources
        if not self.remove_resources(alliance_id, resources):
            return False
            
        # Record distribution
        self.distribution_history[alliance_id].append({
            'from_player_id': player_id,
            'to_player_id': target_id,
            'resources': resources,
            'reason': reason,
            'timestamp': time.time()
        })
        return True

    def get_withdrawal_history(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        """Get recent withdrawal history"""
        if alliance_id not in self.withdrawal_history:
            return []
            
        return sorted(
            self.withdrawal_history[alliance_id],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]

    def get_distribution_history(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        """Get recent distribution history"""
        if alliance_id not in self.distribution_history:
            return []
            
        return sorted(
            self.distribution_history[alliance_id],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]

    def enable_resource_protection(self, alliance_id: str, duration: int = 24 * 3600) -> bool:
        """Enable resource protection for an alliance"""
        if alliance_id not in self.protection_status:
            return False
            
        self.protection_status[alliance_id] = {
            'is_protected': True,
            'protection_end_time': time.time() + duration,
            'last_war_time': time.time()
        }
        return True

    def disable_resource_protection(self, alliance_id: str) -> bool:
        """Disable resource protection for an alliance"""
        if alliance_id not in self.protection_status:
            return False
            
        self.protection_status[alliance_id]['is_protected'] = False
        return True

    def is_protected(self, alliance_id: str) -> bool:
        """Check if alliance resources are protected"""
        if alliance_id not in self.protection_status:
            return False
            
        status = self.protection_status[alliance_id]
        if not status['is_protected']:
            return False
            
        # Check if protection has expired
        if time.time() > status['protection_end_time']:
            status['is_protected'] = False
            return False
            
        return True

    def get_protection_status(self, alliance_id: str) -> Dict:
        """Get current protection status"""
        if alliance_id not in self.protection_status:
            return {}
            
        status = self.protection_status[alliance_id]
        if status['is_protected']:
            time_left = int(status['protection_end_time'] - time.time())
            if time_left > 0:
                return {
                    'is_protected': True,
                    'time_left': time_left
                }
            else:
                status['is_protected'] = False
                
        return {
            'is_protected': False,
            'time_left': 0
        }

    def calculate_war_loot(self, alliance_id: str, attacker_power: float, defender_power: float) -> Dict[str, int]:
        """Calculate resources that can be looted during war"""
        if alliance_id not in self.alliance_resources or self.is_protected(alliance_id):
            return {}
            
        # Calculate loot percentage based on power difference
        power_ratio = attacker_power / (attacker_power + defender_power)
        loot_percentage = min(0.3, power_ratio * 0.5)  # Max 30% loot
        
        # Calculate loot for each resource
        loot = {}
        for resource, amount in self.alliance_resources[alliance_id].items():
            loot[resource] = int(amount * loot_percentage)
            
        return loot

    def apply_war_loot(self, alliance_id: str, loot: Dict[str, int]) -> bool:
        """Apply war loot to alliance resources"""
        if alliance_id not in self.alliance_resources:
            return False
            
        # Remove looted resources
        for resource, amount in loot.items():
            if resource in self.alliance_resources[alliance_id]:
                self.alliance_resources[alliance_id][resource] = max(
                    0,
                    self.alliance_resources[alliance_id][resource] - amount
                )
        return True 