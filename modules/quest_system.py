from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union
import json
from enum import Enum

class QuestType(Enum):
    TUTORIAL = "tutorial"
    DAILY = "daily"
    WEEKLY = "weekly"

@dataclass
class QuestRequirement:
    metric: str
    target: int

@dataclass
class QuestReward:
    gold: Optional[int] = None
    food: Optional[int] = None
    wood: Optional[int] = None
    premium: Optional[int] = None
    strategyPoints: Optional[int] = None

@dataclass
class Quest:
    id: str
    type: QuestType
    title: str
    description: str
    requirements: List[QuestRequirement]
    reward: QuestReward
    isRepeatable: bool
    resetRule: Optional[str] = None
    completed: bool = False
    progress: Dict[str, int] = None

    def __post_init__(self):
        if self.progress is None:
            self.progress = {req.metric: 0 for req in self.requirements}

    def update_progress(self, metric: str, value: int) -> bool:
        """Update progress for a specific metric and check if quest is completed."""
        if metric in self.progress:
            self.progress[metric] = value
            return self.check_completion()
        return False

    def check_completion(self) -> bool:
        """Check if all requirements are met."""
        for req in self.requirements:
            if self.progress.get(req.metric, 0) < req.target:
                return False
        self.completed = True
        return True

class QuestSystem:
    def __init__(self):
        self.quests: Dict[str, Quest] = {}
        self.active_quests: Dict[str, Quest] = {}
        self.completed_quests: Dict[str, Quest] = {}
        self._load_quests()

    def _load_quests(self):
        """Load quest definitions from a configuration file."""
        # TODO: Load from a configuration file
        # For now, we'll use the example quests
        self._add_quest(Quest(
            id="Q_TUT_01",
            type=QuestType.TUTORIAL,
            title="Set Your Commander Name",
            description="Choose a Commander Name to begin your journey.",
            requirements=[QuestRequirement(metric="name_set", target=1)],
            reward=QuestReward(gold=100, food=100),
            isRepeatable=False
        ))

        self._add_quest(Quest(
            id="Q_DLY_01",
            type=QuestType.DAILY,
            title="Collect 1,000 Wood",
            description="Gather 1,000 Wood from your Mine.",
            requirements=[QuestRequirement(metric="wood_collected", target=1000)],
            reward=QuestReward(food=200, strategyPoints=5),
            isRepeatable=True,
            resetRule="RRULE:FREQ=DAILY;BYHOUR=0;BYMINUTE=0;BYSECOND=0"
        ))

        self._add_quest(Quest(
            id="Q_WEK_01",
            type=QuestType.WEEKLY,
            title="Win 3 PvP Battles",
            description="Defeat enemy Commanders in PvP 3 times.",
            requirements=[QuestRequirement(metric="pvp_wins", target=3)],
            reward=QuestReward(gold=500, premium=1),
            isRepeatable=True,
            resetRule="RRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=0;BYMINUTE=0;BYSECOND=0"
        ))

    def _add_quest(self, quest: Quest):
        """Add a quest to the system."""
        self.quests[quest.id] = quest
        if quest.type == QuestType.TUTORIAL:
            self.active_quests[quest.id] = quest

    def get_available_quests(self) -> List[Quest]:
        """Get all available quests for the player."""
        return list(self.quests.values())

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests for the player."""
        return list(self.active_quests.values())

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests for the player."""
        return list(self.completed_quests.values())

    def update_quest_progress(self, quest_id: str, metric: str, value: int) -> Optional[QuestReward]:
        """Update progress for a quest and return reward if completed."""
        quest = self.active_quests.get(quest_id)
        if not quest:
            return None

        if quest.update_progress(metric, value):
            reward = quest.reward
            if not quest.isRepeatable:
                self.completed_quests[quest_id] = quest
                del self.active_quests[quest_id]
            return reward
        return None

    def activate_quest(self, quest_id: str) -> bool:
        """Activate a quest if it's available and not already active."""
        quest = self.quests.get(quest_id)
        if not quest or quest_id in self.active_quests:
            return False

        self.active_quests[quest_id] = quest
        return True

    def reset_daily_quests(self):
        """Reset daily quests based on their reset rules."""
        current_time = datetime.now()
        for quest_id, quest in list(self.active_quests.items()):
            if quest.type == QuestType.DAILY:
                # TODO: Implement proper RRULE parsing and checking
                # For now, we'll just reset all daily quests
                quest.completed = False
                quest.progress = {req.metric: 0 for req in quest.requirements}

    def reset_weekly_quests(self):
        """Reset weekly quests based on their reset rules."""
        current_time = datetime.now()
        for quest_id, quest in list(self.active_quests.items()):
            if quest.type == QuestType.WEEKLY:
                # TODO: Implement proper RRULE parsing and checking
                # For now, we'll just reset all weekly quests
                quest.completed = False
                quest.progress = {req.metric: 0 for req in quest.requirements}

    def display_quest(self, quest: Quest) -> str:
        """Format a single quest for display."""
        status = "Completed" if quest.completed else "In Progress"
        progress_str = []
        for req in quest.requirements:
            current = quest.progress.get(req.metric, 0)
            progress_str.append(f"{req.metric}: {current}/{req.target}")
        
        reward_str = []
        if quest.reward.gold:
            reward_str.append(f"Gold: {quest.reward.gold}")
        if quest.reward.food:
            reward_str.append(f"Food: {quest.reward.food}")
        if quest.reward.wood:
            reward_str.append(f"Wood: {quest.reward.wood}")
        if quest.reward.premium:
            reward_str.append(f"Premium: {quest.reward.premium}")
        if quest.reward.strategyPoints:
            reward_str.append(f"Strategy Points: {quest.reward.strategyPoints}")

        return f"""
Quest: {quest.title} ({quest.id})
Type: {quest.type.value}
Status: {status}
Description: {quest.description}
Progress: {', '.join(progress_str)}
Reward: {', '.join(reward_str)}
"""

    def display_all_quests(self) -> str:
        """Display all quests in the system."""
        output = []
        
        # Tutorial Quests
        tutorial_quests = [q for q in self.quests.values() if q.type == QuestType.TUTORIAL]
        if tutorial_quests:
            output.append("\n=== Tutorial Quests ===")
            for quest in tutorial_quests:
                output.append(self.display_quest(quest))

        # Daily Quests
        daily_quests = [q for q in self.quests.values() if q.type == QuestType.DAILY]
        if daily_quests:
            output.append("\n=== Daily Quests ===")
            for quest in daily_quests:
                output.append(self.display_quest(quest))

        # Weekly Quests
        weekly_quests = [q for q in self.quests.values() if q.type == QuestType.WEEKLY]
        if weekly_quests:
            output.append("\n=== Weekly Quests ===")
            for quest in weekly_quests:
                output.append(self.display_quest(quest))

        return "\n".join(output)

    def display_active_quests(self) -> str:
        """Display only active quests."""
        if not self.active_quests:
            return "No active quests."
        
        output = ["\n=== Active Quests ==="]
        for quest in self.active_quests.values():
            output.append(self.display_quest(quest))
        return "\n".join(output)

    def display_completed_quests(self) -> str:
        """Display completed quests."""
        if not self.completed_quests:
            return "No completed quests."
        
        output = ["\n=== Completed Quests ==="]
        for quest in self.completed_quests.values():
            output.append(self.display_quest(quest))
        return "\n".join(output) 