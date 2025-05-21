"""
Progression Manager Module
Handles player progression, skills, and prestige (per-player)
"""

from typing import Dict, List, Optional
import json
import os

class ProgressionManager:
    def __init__(self):
        self.progression: Dict[str, Dict] = {}
        self.levels = {
            1: {"xp_required": 0, "rewards": {"coins": 100}},
            2: {"xp_required": 100, "rewards": {"coins": 200}},
            3: {"xp_required": 300, "rewards": {"coins": 300}},
            4: {"xp_required": 600, "rewards": {"coins": 400}},
            5: {"xp_required": 1000, "rewards": {"coins": 500}},
            6: {"xp_required": 1500, "rewards": {"coins": 600}},
            7: {"xp_required": 2100, "rewards": {"coins": 700}},
            8: {"xp_required": 2800, "rewards": {"coins": 800}},
            9: {"xp_required": 3600, "rewards": {"coins": 900}},
            10: {"xp_required": 4500, "rewards": {"coins": 1000, "hustlecoins": 5}}
        }
        self.player_data_file = "data/player_progression.json"
        self._ensure_data_directory()
        self._load_player_data()

    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.player_data_file), exist_ok=True)

    def _load_player_data(self):
        """Load player progression data from file"""
        try:
            with open(self.player_data_file, 'r') as f:
                self.player_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.player_data = {}

    def _save_player_data(self):
        """Save player progression data to file"""
        with open(self.player_data_file, 'w') as f:
            json.dump(self.player_data, f, indent=4)

    def get_player_progression(self, player_id: str) -> Dict:
        return self.progression.get(player_id, {})

    def set_player_progression(self, player_id: str, data: Dict):
        self.progression[player_id] = data

    def get_player_level(self, player_id: int) -> int:
        """Get player's current level"""
        if str(player_id) not in self.player_data:
            self.player_data[str(player_id)] = {"level": 1, "xp": 0}
            self._save_player_data()
        return self.player_data[str(player_id)]["level"]

    def get_player_xp(self, player_id: int) -> int:
        """Get player's current XP"""
        if str(player_id) not in self.player_data:
            self.player_data[str(player_id)] = {"level": 1, "xp": 0}
            self._save_player_data()
        return self.player_data[str(player_id)]["xp"]

    def add_xp(self, player_id: int, xp_amount: int) -> Dict:
        """Add XP to player and handle level ups"""
        player_id = str(player_id)
        if player_id not in self.player_data:
            self.player_data[player_id] = {"level": 1, "xp": 0}

        current_level = self.player_data[player_id]["level"]
        current_xp = self.player_data[player_id]["xp"]
        new_xp = current_xp + xp_amount
        
        # Check for level ups
        rewards = {}
        while current_level < 10 and new_xp >= self.levels[current_level + 1]["xp_required"]:
            current_level += 1
            level_rewards = self.levels[current_level]["rewards"]
            for reward_type, amount in level_rewards.items():
                rewards[reward_type] = rewards.get(reward_type, 0) + amount

        # Update player data
        self.player_data[player_id] = {
            "level": current_level,
            "xp": new_xp
        }
        self._save_player_data()

        return {
            "old_level": self.player_data[player_id]["level"],
            "new_level": current_level,
            "old_xp": current_xp,
            "new_xp": new_xp,
            "rewards": rewards
        }

    def get_level_info(self, level: int) -> Optional[Dict]:
        """Get information about a specific level"""
        return self.levels.get(level)

    def get_next_level_xp(self, player_id: int) -> int:
        """Get XP required for next level"""
        current_level = self.get_player_level(player_id)
        if current_level >= 10:
            return 0
        return self.levels[current_level + 1]["xp_required"]

    def get_level_progress(self, player_id: int) -> Dict:
        """Get player's level progress information"""
        current_level = self.get_player_level(player_id)
        current_xp = self.get_player_xp(player_id)
        next_level_xp = self.get_next_level_xp(player_id)
        
        if current_level >= 10:
            return {
                "level": current_level,
                "xp": current_xp,
                "next_level_xp": 0,
                "progress_percentage": 100
            }

        current_level_xp = self.levels[current_level]["xp_required"]
        xp_for_next_level = next_level_xp - current_level_xp
        xp_progress = current_xp - current_level_xp
        progress_percentage = (xp_progress / xp_for_next_level) * 100

        return {
            "level": current_level,
            "xp": current_xp,
            "next_level_xp": next_level_xp,
            "progress_percentage": round(progress_percentage, 1)
        } 