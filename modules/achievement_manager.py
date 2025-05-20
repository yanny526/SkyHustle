"""
Achievement Manager Module
Handles player achievements, progress tracking, and rewards
"""

import time
from typing import Dict, List, Optional
from config.game_config import ACHIEVEMENTS
from modules.google_sheets_manager import GoogleSheetsManager
from modules.game_logging import log_achievement

class AchievementManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

    def get_player_achievements(self, player_id: str) -> Dict:
        records = self.sheets.get_worksheet('Achievements').get_all_records()
        player_achievements = set(r['achievement'] for r in records if r['player_id'] == player_id)
        achievements = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            status = {
                'id': achievement_id,
                'name': achievement['name'],
                'description': achievement['description'],
                'emoji': achievement['emoji'],
                'reward': achievement['reward'],
                'completed': achievement['name'] in player_achievements
            }
            achievements.append(status)
        return {'success': True, 'achievements': achievements}

    def update_progress(self, player_id: str, achievement_type: str, amount: int = 1) -> Dict:
        # For each achievement of this type, check if completed and log if new
        updated = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_type in achievement_id:
                # Check if already logged
                records = self.sheets.get_worksheet('Achievements').get_all_records()
                already_logged = any(r['player_id'] == player_id and r['achievement'] == achievement['name'] for r in records)
                if already_logged:
                    continue
                # Check completion
                if self._check_completion(achievement_id, amount):
                    log_achievement(player_id, achievement['name'])
                    updated.append(achievement_id)
                    # Update player progress in Players tab
                    player = self.sheets.get_player(player_id)
                    if player:
                        player['achievements'] = player.get('achievements', '') + f',{achievement_id}' if player.get('achievements') else achievement_id
                        self.sheets.upsert_player(player)
        return {'success': True, 'updated': updated}

    def claim_reward(self, player_id: str, achievement_id: str) -> Dict:
        achievement = ACHIEVEMENTS.get(achievement_id)
        if not achievement:
            return {'success': False, 'message': 'Invalid achievement ID'}
        records = self.sheets.get_worksheet('Achievements').get_all_records()
        already_logged = any(r['player_id'] == player_id and r['achievement'] == achievement['name'] for r in records)
        if not already_logged:
            return {'success': False, 'message': 'Achievement not completed'}
        # Rewards are now tracked in the sheet; just return the reward
        return {'success': True, 'reward': achievement['reward']}

    def get_achievement_progress(self, player_id: str, achievement_id: str) -> Dict:
        achievement = ACHIEVEMENTS.get(achievement_id)
        if not achievement:
            return {'success': False, 'message': 'Invalid achievement ID'}
        records = self.sheets.get_worksheet('Achievements').get_all_records()
        completed = any(r['player_id'] == player_id and r['achievement'] == achievement['name'] for r in records)
        return {'success': True, 'completed': completed}

    def _check_completion(self, achievement_id: str, progress: int) -> bool:
        achievement = ACHIEVEMENTS[achievement_id]
        if 'first_building' in achievement_id:
            return progress >= 1
        elif 'resource_master' in achievement_id:
            return progress >= 1000
        elif 'military_power' in achievement_id:
            return progress >= 10
        elif 'combat_veteran' in achievement_id:
            return progress >= 10
        elif 'league_champion' in achievement_id:
            return progress >= 1
        return False 