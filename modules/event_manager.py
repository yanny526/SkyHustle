"""
Event Manager for SkyHustle 2
Handles game events, special events, and event rewards
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class EventManager:
    def __init__(self):
        self.active_events: Dict[str, Dict] = {}
        self.event_history: List[Dict] = []
        self.event_types = {
            'resource_boost': {
                'name': 'Resource Boost',
                'duration': 24,  # hours
                'description': 'Double resource production for 24 hours'
            },
            'combat_bonus': {
                'name': 'Combat Bonus',
                'duration': 12,  # hours
                'description': '50% increased combat power for 12 hours'
            },
            'research_discount': {
                'name': 'Research Discount',
                'duration': 48,  # hours
                'description': '25% reduced research costs for 48 hours'
            },
            'alliance_bonus': {
                'name': 'Alliance Bonus',
                'duration': 72,  # hours
                'description': 'Increased alliance benefits and rewards'
            }
        }

    async def start_event(self, event_type: str, duration: Optional[int] = None) -> Dict:
        """Start a new event"""
        if event_type not in self.event_types:
            raise ValueError(f"Invalid event type: {event_type}")

        event_info = self.event_types[event_type].copy()
        if duration:
            event_info['duration'] = duration

        event = {
            'type': event_type,
            'name': event_info['name'],
            'description': event_info['description'],
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=event_info['duration']),
            'active': True
        }

        self.active_events[event_type] = event
        self.event_history.append(event)
        return event

    async def end_event(self, event_type: str) -> None:
        """End an active event"""
        if event_type in self.active_events:
            self.active_events[event_type]['active'] = False
            self.active_events[event_type]['end_time'] = datetime.now()

    async def get_active_events(self) -> List[Dict]:
        """Get all currently active events"""
        return [event for event in self.active_events.values() if event['active']]

    async def is_event_active(self, event_type: str) -> bool:
        """Check if a specific event is active"""
        return event_type in self.active_events and self.active_events[event_type]['active']

    async def get_event_multiplier(self, event_type: str) -> float:
        """Get the multiplier for a specific event type"""
        if not await self.is_event_active(event_type):
            return 1.0

        multipliers = {
            'resource_boost': 2.0,
            'combat_bonus': 1.5,
            'research_discount': 0.75,
            'alliance_bonus': 1.25
        }
        return multipliers.get(event_type, 1.0)

    async def cleanup_expired_events(self) -> None:
        """Clean up expired events"""
        current_time = datetime.now()
        for event_type, event in list(self.active_events.items()):
            if event['end_time'] <= current_time:
                await self.end_event(event_type)

    async def get_event_history(self, limit: int = 10) -> List[Dict]:
        """Get recent event history"""
        return sorted(
            self.event_history,
            key=lambda x: x['start_time'],
            reverse=True
        )[:limit]

    async def get_random_event(self) -> Tuple[str, Dict]:
        """Get a random event type and its info"""
        event_type = random.choice(list(self.event_types.keys()))
        return event_type, self.event_types[event_type] 