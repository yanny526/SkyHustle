"""
Daily Rewards Manager Module
Handles daily rewards, streaks, and bonus rewards
"""

import time
from typing import Dict, Optional
from config.game_config import DAILY_REWARDS

class DailyRewardsManager:
    def __init__(self):
        self.last_claim = {}  # Store last claim time for each player
        self.streaks = {}     # Store current streak for each player
        self.claimed = {}     # Store claimed rewards for each player

    def can_claim_reward(self, player_id: str) -> Dict:
        """Check if player can claim daily reward"""
        current_time = time.time()
        
        # Initialize player data if not exists
        if player_id not in self.last_claim:
            self.last_claim[player_id] = 0
            self.streaks[player_id] = 0
            self.claimed[player_id] = set()
            return {'success': True, 'can_claim': True}

        # Check if 24 hours have passed since last claim
        time_since_last_claim = current_time - self.last_claim[player_id]
        if time_since_last_claim < 86400:  # 24 hours in seconds
            time_left = 86400 - time_since_last_claim
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            return {
                'success': True,
                'can_claim': False,
                'time_left': f"{hours}h {minutes}m"
            }

        # Check if streak is broken (more than 48 hours since last claim)
        if time_since_last_claim > 172800:  # 48 hours in seconds
            self.streaks[player_id] = 0

        return {'success': True, 'can_claim': True}

    def claim_reward(self, player_id: str) -> Dict:
        """Claim daily reward"""
        # Check if can claim
        check_result = self.can_claim_reward(player_id)
        if not check_result['success'] or not check_result['can_claim']:
            return check_result

        # Update streak
        self.streaks[player_id] = (self.streaks[player_id] % 7) + 1
        current_streak = self.streaks[player_id]

        # Get reward for current streak
        reward = DAILY_REWARDS[current_streak]

        # Update last claim time
        self.last_claim[player_id] = time.time()

        # Add to claimed rewards
        if player_id not in self.claimed:
            self.claimed[player_id] = set()
        self.claimed[player_id].add(current_streak)

        return {
            'success': True,
            'streak': current_streak,
            'reward': reward,
            'is_seventh_day': current_streak == 7
        }

    def get_streak_info(self, player_id: str) -> Dict:
        """Get player's streak information"""
        if player_id not in self.streaks:
            return {
                'success': True,
                'streak': 0,
                'next_reward': DAILY_REWARDS[1]
            }

        current_streak = self.streaks[player_id]
        next_streak = (current_streak % 7) + 1

        return {
            'success': True,
            'streak': current_streak,
            'next_reward': DAILY_REWARDS[next_streak],
            'time_since_last_claim': time.time() - self.last_claim.get(player_id, 0)
        }

    def get_claimed_rewards(self, player_id: str) -> Dict:
        """Get list of claimed rewards for player"""
        if player_id not in self.claimed:
            return {'success': True, 'claimed': []}

        claimed = []
        for day in sorted(self.claimed[player_id]):
            claimed.append({
                'day': day,
                'reward': DAILY_REWARDS[day]
            })

        return {
            'success': True,
            'claimed': claimed
        } 