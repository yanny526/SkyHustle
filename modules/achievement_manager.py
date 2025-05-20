"""
Achievement Manager Module
Handles player achievements, progress tracking, and rewards
"""

import time
from typing import Dict, List, Optional
from config.game_config import ACHIEVEMENTS

class AchievementManager:
    def __init__(self):
        self.achievements = {}  # Store player achievements
        self.progress = {}      # Store achievement progress
        self.rewards = {}       # Store claimed rewards

    def get_player_achievements(self, player_id: str) -> Dict:
        """Get all achievements for a player"""
        if player_id not in self.achievements:
            self.achievements[player_id] = set()
            self.progress[player_id] = {}
            self.rewards[player_id] = set()

        # Get all achievements with their status
        player_achievements = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            status = {
                'id': achievement_id,
                'name': achievement['name'],
                'description': achievement['description'],
                'emoji': achievement['emoji'],
                'reward': achievement['reward'],
                'completed': achievement_id in self.achievements[player_id],
                'reward_claimed': achievement_id in self.rewards[player_id],
                'progress': self.progress[player_id].get(achievement_id, 0)
            }
            player_achievements.append(status)

        return {
            'success': True,
            'achievements': player_achievements
        }

    def update_progress(self, player_id: str, achievement_type: str, amount: int = 1) -> Dict:
        """Update progress for an achievement"""
        if player_id not in self.progress:
            self.progress[player_id] = {}

        # Update progress for all achievements of this type
        updated = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_id in self.achievements[player_id]:
                continue  # Skip completed achievements

            if achievement_type in achievement_id:
                current_progress = self.progress[player_id].get(achievement_id, 0)
                new_progress = current_progress + amount
                self.progress[player_id][achievement_id] = new_progress

                # Check if achievement is completed
                if self._check_completion(achievement_id, new_progress):
                    self.achievements[player_id].add(achievement_id)
                    updated.append(achievement_id)

        return {
            'success': True,
            'updated': updated
        }

    def claim_reward(self, player_id: str, achievement_id: str) -> Dict:
        """Claim reward for a completed achievement"""
        if achievement_id not in ACHIEVEMENTS:
            return {'success': False, 'message': 'Invalid achievement ID'}

        if achievement_id not in self.achievements.get(player_id, set()):
            return {'success': False, 'message': 'Achievement not completed'}

        if achievement_id in self.rewards.get(player_id, set()):
            return {'success': False, 'message': 'Reward already claimed'}

        # Add achievement to claimed rewards
        if player_id not in self.rewards:
            self.rewards[player_id] = set()
        self.rewards[player_id].add(achievement_id)

        return {
            'success': True,
            'reward': ACHIEVEMENTS[achievement_id]['reward']
        }

    def get_achievement_progress(self, player_id: str, achievement_id: str) -> Dict:
        """Get progress for a specific achievement"""
        if achievement_id not in ACHIEVEMENTS:
            return {'success': False, 'message': 'Invalid achievement ID'}

        progress = self.progress.get(player_id, {}).get(achievement_id, 0)
        completed = achievement_id in self.achievements.get(player_id, set())
        reward_claimed = achievement_id in self.rewards.get(player_id, set())

        return {
            'success': True,
            'progress': progress,
            'completed': completed,
            'reward_claimed': reward_claimed
        }

    def _check_completion(self, achievement_id: str, progress: int) -> bool:
        """Check if an achievement is completed based on its type"""
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