"""
Bag Manager for SkyHustle 2
Handles player inventory (bag), item usage, and item tracking
"""

import time
from typing import Dict, List, Optional

class BagManager:
    def __init__(self):
        self.bags: Dict[str, Dict[str, Dict]] = {}  # player_id -> item_id -> item info

    def add_item(self, player_id: str, item_id: str, item_type: str, quantity: int = 1, duration: Optional[int] = None):
        """Add an item to the player's bag"""
        if player_id not in self.bags:
            self.bags[player_id] = {}
        if item_id not in self.bags[player_id]:
            self.bags[player_id][item_id] = {
                'type': item_type,  # 'single', 'multi', 'timed'
                'quantity': 0,
                'added_at': time.time(),
                'duration': duration,  # For timed items (seconds)
                'active_until': None
            }
        self.bags[player_id][item_id]['quantity'] += quantity
        if item_type == 'timed' and duration:
            self.bags[player_id][item_id]['active_until'] = time.time() + duration

    def use_item(self, player_id: str, item_id: str) -> bool:
        """Use an item from the player's bag. Returns True if used, False if not available."""
        if player_id not in self.bags or item_id not in self.bags[player_id]:
            return False
        item = self.bags[player_id][item_id]
        if item['type'] == 'single':
            if item['quantity'] <= 0:
                return False
            item['quantity'] -= 1
            if item['quantity'] == 0:
                del self.bags[player_id][item_id]
            return True
        elif item['type'] == 'multi':
            if item['quantity'] <= 0:
                return False
            item['quantity'] -= 1
            if item['quantity'] == 0:
                del self.bags[player_id][item_id]
            return True
        elif item['type'] == 'timed':
            # Activate or refresh the timed effect
            if item['duration']:
                item['active_until'] = time.time() + item['duration']
            return True
        return False

    def get_bag(self, player_id: str) -> List[Dict]:
        """Get a list of items in the player's bag"""
        if player_id not in self.bags:
            return []
        bag = []
        for item_id, item in self.bags[player_id].items():
            entry = {
                'item_id': item_id,
                'type': item['type'],
                'quantity': item['quantity'],
                'active_until': item.get('active_until'),
                'duration': item.get('duration')
            }
            bag.append(entry)
        return bag

    def remove_item(self, player_id: str, item_id: str, quantity: int = 1) -> bool:
        """Remove a quantity of an item from the player's bag"""
        if player_id not in self.bags or item_id not in self.bags[player_id]:
            return False
        item = self.bags[player_id][item_id]
        if item['quantity'] < quantity:
            return False
        item['quantity'] -= quantity
        if item['quantity'] == 0:
            del self.bags[player_id][item_id]
        return True

    def has_item(self, player_id: str, item_id: str) -> bool:
        """Check if the player has at least one of the item"""
        return player_id in self.bags and item_id in self.bags[player_id] and self.bags[player_id][item_id]['quantity'] > 0 