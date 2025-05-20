"""
Alliance Benefits Manager for SkyHustle 2
Handles alliance benefits, perks, and bonuses for members
"""

from typing import Dict, List, Optional
import time
from config.alliance_config import ALLIANCE_SETTINGS

class AllianceBenefitsManager:
    def __init__(self):
        self.active_benefits: Dict[str, Dict] = {}  # alliance_id -> benefits
        self.member_bonuses: Dict[str, Dict] = {}  # player_id -> bonuses
        self.alliance_perks: Dict[str, List[str]] = {}  # alliance_id -> list of active perks
        self.perk_cooldowns: Dict[str, Dict[str, float]] = {}  # alliance_id -> {perk_id: cooldown_end_time}
        self.last_bonus_update: Dict[str, Dict[str, float]] = {}  # player_id -> {bonus_type: last_update_time}

    def calculate_alliance_benefits(self, alliance_id: str, alliance_level: int, alliance_xp: int) -> Dict:
        """Calculate benefits based on alliance level and XP"""
        benefits = {
            'resource_bonus': min(alliance_level * ALLIANCE_SETTINGS['resource_bonus_per_level'], 0.5),  # Max 50%
            'xp_bonus': min(alliance_level * ALLIANCE_SETTINGS['xp_bonus_per_level'], 0.3),  # Max 30%
            'production_bonus': min(alliance_level * 0.02, 0.5),  # Max 50% production bonus
            'research_bonus': min(alliance_level * 0.01, 0.25),  # Max 25% research speed bonus
            'combat_bonus': min(alliance_level * 0.015, 0.3),  # Max 30% combat power bonus
            'defense_bonus': min(alliance_level * 0.015, 0.3),  # Max 30% defense bonus
        }
        
        # Add XP milestone bonuses
        xp_milestones = [10000, 50000, 100000, 500000, 1000000]
        for milestone in xp_milestones:
            if alliance_xp >= milestone:
                benefits['resource_bonus'] = min(benefits['resource_bonus'] + 0.05, 0.5)  # Cap at 50%
        
        self.active_benefits[alliance_id] = benefits
        return benefits

    def get_member_benefits(self, player_id: str, alliance_id: str) -> Dict:
        """Get benefits for a specific alliance member"""
        if alliance_id not in self.active_benefits:
            return {}
        
        base_benefits = self.active_benefits[alliance_id].copy()
        
        # Add member-specific bonuses
        if player_id in self.member_bonuses:
            for bonus_type, amount in self.member_bonuses[player_id].items():
                if bonus_type in base_benefits:
                    base_benefits[bonus_type] += amount
        
        return base_benefits

    def add_member_bonus(self, player_id: str, bonus_type: str, amount: float) -> bool:
        """Add a temporary bonus for a specific member"""
        if player_id not in self.member_bonuses:
            self.member_bonuses[player_id] = {}
        
        if bonus_type not in self.member_bonuses[player_id]:
            self.member_bonuses[player_id][bonus_type] = 0
        
        # Check bonus cap
        current_bonus = self.member_bonuses[player_id][bonus_type]
        max_bonus = self._get_max_bonus(bonus_type)
        if current_bonus + amount > max_bonus:
            amount = max_bonus - current_bonus
        
        self.member_bonuses[player_id][bonus_type] += amount
        return True

    def remove_member_bonus(self, player_id: str, bonus_type: str, amount: float) -> bool:
        """Remove a temporary bonus for a specific member"""
        if player_id not in self.member_bonuses or bonus_type not in self.member_bonuses[player_id]:
            return False
        
        self.member_bonuses[player_id][bonus_type] = max(0, self.member_bonuses[player_id][bonus_type] - amount)
        return True

    def unlock_alliance_perk(self, alliance_id: str, perk_id: str) -> bool:
        """Unlock a special perk for the alliance"""
        if alliance_id not in self.alliance_perks:
            self.alliance_perks[alliance_id] = []
        
        # Check if perk is already unlocked
        if perk_id in self.alliance_perks[alliance_id]:
            return False
            
        # Check perk cooldown
        current_time = time.time()
        if alliance_id in self.perk_cooldowns and perk_id in self.perk_cooldowns[alliance_id]:
            if current_time < self.perk_cooldowns[alliance_id][perk_id]:
                return False
        
        # Validate perk exists
        if perk_id not in ALLIANCE_SETTINGS['perks']:
            return False
            
        self.alliance_perks[alliance_id].append(perk_id)
        
        # Set perk cooldown
        if alliance_id not in self.perk_cooldowns:
            self.perk_cooldowns[alliance_id] = {}
        self.perk_cooldowns[alliance_id][perk_id] = current_time + 86400  # 24 hour cooldown
        
        return True

    def _get_max_bonus(self, bonus_type: str) -> float:
        """Get maximum allowed bonus for a specific type"""
        bonus_caps = {
            'resource_bonus': 0.5,  # 50% max
            'xp_bonus': 0.3,        # 30% max
            'production_bonus': 0.5, # 50% max
            'research_bonus': 0.25,  # 25% max
            'combat_bonus': 0.3,     # 30% max
            'defense_bonus': 0.3     # 30% max
        }
        return bonus_caps.get(bonus_type, 0.0)

    def get_alliance_perks(self, alliance_id: str) -> List[str]:
        """Get list of unlocked perks for an alliance"""
        return self.alliance_perks.get(alliance_id, [])

    def apply_benefits_to_resources(self, player_id: str, resources: Dict[str, int]) -> Dict[str, int]:
        """Apply alliance benefits to resource production"""
        if player_id not in self.member_bonuses:
            return resources
        
        benefits = self.member_bonuses[player_id]
        if 'resource_bonus' not in benefits:
            return resources
        
        bonus = 1 + benefits['resource_bonus']
        return {resource: int(amount * bonus) for resource, amount in resources.items()}

    def apply_benefits_to_xp(self, player_id: str, xp_amount: int) -> int:
        """Apply alliance benefits to XP gain"""
        if player_id not in self.member_bonuses:
            return xp_amount
        
        benefits = self.member_bonuses[player_id]
        if 'xp_bonus' not in benefits:
            return xp_amount
        
        bonus = 1 + benefits['xp_bonus']
        return int(xp_amount * bonus)

    def apply_benefits_to_combat(self, player_id: str, combat_power: float) -> float:
        """Apply alliance benefits to combat power"""
        if player_id not in self.member_bonuses:
            return combat_power
        
        benefits = self.member_bonuses[player_id]
        if 'combat_bonus' not in benefits:
            return combat_power
        
        bonus = 1 + benefits['combat_bonus']
        return combat_power * bonus

    def apply_benefits_to_defense(self, player_id: str, defense_power: float) -> float:
        """Apply alliance benefits to defense power"""
        if player_id not in self.member_bonuses:
            return defense_power
        
        benefits = self.member_bonuses[player_id]
        if 'defense_bonus' not in benefits:
            return defense_power
        
        bonus = 1 + benefits['defense_bonus']
        return defense_power * bonus

    def apply_benefits_to_research(self, player_id: str, research_time: int) -> int:
        """Apply alliance benefits to research time"""
        if player_id not in self.member_bonuses:
            return research_time
        
        benefits = self.member_bonuses[player_id]
        if 'research_bonus' not in benefits:
            return research_time
        
        bonus = 1 - benefits['research_bonus']  # Reduce time by bonus percentage
        return int(research_time * bonus) 