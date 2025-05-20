"""
Black Market Manager for SkyHustle 2
Handles the premium shop (HustleCoins-based purchases, rare/rotating items)
"""

import time
import random
from typing import Dict, List
from modules.bag_manager import BagManager
from modules.player_manager import PlayerManager

BLACK_MARKET_ITEMS = [
    {
        'item_id': 'revival_potion',
        'name': 'Revival Potion',
        'description': 'Revives all soldiers lost in your latest battle. Single-use.',
        'cost': 5,
        'type': 'single',
        'quantity': 1
    },
    {
        'item_id': 'rare_tank',
        'name': 'Rare Tank',
        'description': 'A powerful tank unit. Limited to 1 per player.',
        'cost': 10,
        'type': 'single',
        'quantity': 1
    },
    {
        'item_id': 'speedup_8h',
        'name': '8h Speedup',
        'description': 'Reduces any timer by 8 hours.',
        'cost': 3,
        'type': 'single',
        'quantity': 1
    },
    {
        'item_id': 'resource_boost_7d',
        'name': '7d Resource Boost',
        'description': 'Increases resource production by 5% for 7 days.',
        'cost': 8,
        'type': 'timed',
        'quantity': 1,
        'duration': 7*24*3600
    },
    {
        'item_id': 'mystery_box',
        'name': 'Mystery Box',
        'description': 'Contains a random rare item or unit.',
        'cost': 4,
        'type': 'single',
        'quantity': 1
    },
    {
        'item_id': 'cosmetic_banner',
        'name': 'Exclusive Banner',
        'description': 'A unique banner for your base. Permanent.',
        'cost': 6,
        'type': 'single',
        'quantity': 1
    }
]

class BlackMarketManager:
    def __init__(self, bag_manager: BagManager, player_manager: PlayerManager):
        self.bag_manager = bag_manager
        self.player_manager = player_manager
        self.rotation_seed = int(time.time() // (7*24*3600))  # Rotates weekly

    def get_market_items(self) -> List[Dict]:
        """Return a rotating list of 4 items for this week"""
        random.seed(self.rotation_seed)
        return random.sample(BLACK_MARKET_ITEMS, 4)

    def get_item_info(self, item_id: str) -> Dict:
        for item in BLACK_MARKET_ITEMS:
            if item['item_id'] == item_id:
                return item
        return {}

    def purchase_item(self, player_id: str, item_id: str) -> Dict:
        item = self.get_item_info(item_id)
        if not item:
            return {'success': False, 'message': 'Item not found.'}
        # Check if player can afford
        if self.player_manager.get_hustlecoins(player_id) < item['cost']:
            return {'success': False, 'message': 'Not enough HustleCoins.'}
        # Special rule: rare_tank limited to 1 per player
        if item_id == 'rare_tank' and self.bag_manager.has_item(player_id, 'rare_tank'):
            return {'success': False, 'message': 'You already own a Rare Tank.'}
        # Spend HustleCoins
        self.player_manager.spend_hustlecoins(player_id, item['cost'])
        # Add item to bag
        self.bag_manager.add_item(player_id, item_id, item['type'], item['quantity'], item.get('duration'))
        return {'success': True, 'message': f"Purchased {item['name']}!"} 