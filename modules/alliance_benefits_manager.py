"""
Alliance Benefits Manager for SkyHustle 2
Handles alliance benefits, perks, and bonuses for members
"""

from typing import Dict, List, Optional
import time
import json
from config.alliance_config import ALLIANCE_SETTINGS
from modules.google_sheets_manager import GoogleSheetsManager

class AllianceBenefitsManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

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
        
        # Store in Alliances tab
        alliance = self.sheets.get_alliance(alliance_id)
        if alliance:
            alliance['benefits'] = json.dumps(benefits)
            self.sheets.upsert_alliance(alliance)
        return benefits

    def get_member_benefits(self, player_id: str, alliance_id: str) -> Dict:
        """Get benefits for a specific alliance member"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'benefits' not in alliance:
            return {}
        base_benefits = json.loads(alliance['benefits']) if alliance['benefits'] else {}
        player = self.sheets.get_player(player_id)
        member_bonuses = json.loads(player['bonuses']) if player and 'bonuses' in player and player['bonuses'] else {}
        for bonus_type, amount in member_bonuses.items():
            if bonus_type in base_benefits:
                base_benefits[bonus_type] += amount
        return base_benefits

    def add_member_bonus(self, player_id: str, bonus_type: str, amount: float) -> bool:
        """Add a temporary bonus for a specific member"""
        player = self.sheets.get_player(player_id)
        if not player:
            return False
        bonuses = json.loads(player['bonuses']) if 'bonuses' in player and player['bonuses'] else {}
        if bonus_type not in bonuses:
            bonuses[bonus_type] = 0
        current_bonus = bonuses[bonus_type]
        max_bonus = self._get_max_bonus(bonus_type)
        if current_bonus + amount > max_bonus:
            amount = max_bonus - current_bonus
        bonuses[bonus_type] += amount
        player['bonuses'] = json.dumps(bonuses)
        self.sheets.upsert_player(player)
        return True

    def remove_member_bonus(self, player_id: str, bonus_type: str, amount: float) -> bool:
        """Remove a temporary bonus for a specific member"""
        player = self.sheets.get_player(player_id)
        if not player or 'bonuses' not in player:
            return False
        bonuses = json.loads(player['bonuses']) if player['bonuses'] else {}
        if bonus_type not in bonuses:
            return False
        bonuses[bonus_type] = max(0, bonuses[bonus_type] - amount)
        player['bonuses'] = json.dumps(bonuses)
        self.sheets.upsert_player(player)
        return True

    def unlock_alliance_perk(self, alliance_id: str, perk_id: str) -> bool:
        """Unlock a special perk for the alliance"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        perks = json.loads(alliance['perks']) if 'perks' in alliance and alliance['perks'] else []
        perk_cooldowns = json.loads(alliance['perk_cooldowns']) if 'perk_cooldowns' in alliance and alliance['perk_cooldowns'] else {}
        current_time = time.time()
        if perk_id in perks:
            return False
        if perk_id in perk_cooldowns and current_time < perk_cooldowns[perk_id]:
            return False
        if perk_id not in ALLIANCE_SETTINGS['perks']:
            return False
        perks.append(perk_id)
        perk_cooldowns[perk_id] = current_time + 86400  # 24 hour cooldown
        alliance['perks'] = json.dumps(perks)
        alliance['perk_cooldowns'] = json.dumps(perk_cooldowns)
        self.sheets.upsert_alliance(alliance)
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
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'perks' not in alliance:
            return []
        return json.loads(alliance['perks']) if alliance['perks'] else []

    def apply_benefits_to_resources(self, player_id: str, resources: Dict[str, int]) -> Dict[str, int]:
        """Apply alliance benefits to resource production"""
        player = self.sheets.get_player(player_id)
        if not player or 'bonuses' not in player:
            return resources
        
        benefits = json.loads(player['bonuses']) if player['bonuses'] else {}
        if 'resource_bonus' not in benefits:
            return resources
        
        bonus = 1 + benefits['resource_bonus']
        return {resource: int(amount * bonus) for resource, amount in resources.items()}

    def apply_benefits_to_xp(self, player_id: str, xp_amount: int) -> int:
        """Apply alliance benefits to XP gain"""
        player = self.sheets.get_player(player_id)
        if not player or 'bonuses' not in player:
            return xp_amount
        
        benefits = json.loads(player['bonuses']) if player['bonuses'] else {}
        if 'xp_bonus' not in benefits:
            return xp_amount
        
        bonus = 1 + benefits['xp_bonus']
        return int(xp_amount * bonus)

    def apply_benefits_to_combat(self, player_id: str, combat_power: float) -> float:
        """Apply alliance benefits to combat power"""
        player = self.sheets.get_player(player_id)
        if not player or 'bonuses' not in player:
            return combat_power
        
        benefits = json.loads(player['bonuses']) if player['bonuses'] else {}
        if 'combat_bonus' not in benefits:
            return combat_power
        
        bonus = 1 + benefits['combat_bonus']
        return combat_power * bonus

    def apply_benefits_to_defense(self, player_id: str, defense_power: float) -> float:
        """Apply alliance benefits to defense power"""
        player = self.sheets.get_player(player_id)
        if not player or 'bonuses' not in player:
            return defense_power
        
        benefits = json.loads(player['bonuses']) if player['bonuses'] else {}
        if 'defense_bonus' not in benefits:
            return defense_power
        
        bonus = 1 + benefits['defense_bonus']
        return defense_power * bonus

    def apply_benefits_to_research(self, player_id: str, research_time: int) -> int:
        """Apply alliance benefits to research time"""
        player = self.sheets.get_player(player_id)
        if not player or 'bonuses' not in player:
            return research_time
        
        benefits = json.loads(player['bonuses']) if player['bonuses'] else {}
        if 'research_bonus' not in benefits:
            return research_time
        
        bonus = 1 - benefits['research_bonus']  # Reduce time by bonus percentage
        return int(research_time * bonus) 