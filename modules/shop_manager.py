"""
Shop Manager for SkyHustle 2
Handles the regular shop (resource-based purchases)
"""

from typing import Dict, List
from modules.bag_manager import BagManager
from modules.google_sheets_manager import GoogleSheetsManager
import time
import uuid

SHOP_ITEMS = {
    'speedup_5m': {
        'name': '5m Speedup',
        'description': 'Reduces any timer by 5 minutes.',
        'cost': {'wood': 200, 'gold': 100},
        'type': 'single',
        'quantity': 1
    },
    'speedup_1h': {
        'name': '1h Speedup',
        'description': 'Reduces any timer by 1 hour.',
        'cost': {'gold': 1000, 'stone': 500},
        'type': 'single',
        'quantity': 1
    },
    'resource_pack': {
        'name': 'Resource Pack',
        'description': 'Grants 500 wood, 500 stone, 500 food.',
        'cost': {'gold': 1200},
        'type': 'single',
        'quantity': 1
    },
    'army_boost': {
        'name': 'Army Attack Boost',
        'description': 'Increases army attack by 5% for next battle.',
        'cost': {'food': 800, 'gold': 400},
        'type': 'single',
        'quantity': 1
    },
    'instant_build': {
        'name': 'Instant Build (Lv1-5)',
        'description': 'Instantly completes a building upgrade (Lv1-5 only).',
        'cost': {'stone': 1000, 'gold': 800},
        'type': 'single',
        'quantity': 1
    }
}

class ShopManager:
    def __init__(self, bag_manager: BagManager, resource_manager):
        self.bag_manager = bag_manager
        self.resource_manager = resource_manager
        self.sheets = GoogleSheetsManager()

    def get_shop_items(self) -> List[Dict]:
        """Return a list of all shop items"""
        return [dict(item_id=k, **v) for k, v in SHOP_ITEMS.items()]

    def get_item_info(self, item_id: str) -> Dict:
        """Get info for a specific shop item"""
        return SHOP_ITEMS.get(item_id, {})

    def purchase_item(self, player_id: str, item_id: str) -> Dict:
        """Attempt to purchase an item with resources. Returns success and message."""
        item = SHOP_ITEMS.get(item_id)
        if not item:
            return {'success': False, 'message': 'Item not found.'}
        # Check if player can afford
        if not self.resource_manager.can_afford(player_id, item['cost']):
            return {'success': False, 'message': 'Not enough resources.'}
        # Spend resources
        self.resource_manager.spend_resources(player_id, item['cost'])
        # Add item to bag
        self.bag_manager.add_item(player_id, item_id, item['type'], item['quantity'])
        # Log transaction
        tx_data = {
            'transaction_id': str(uuid.uuid4()),
            'player_id': player_id,
            'item_id': item_id,
            'item_name': item['name'],
            'quantity': item['quantity'],
            'cost': str(item['cost']),
            'currency': 'resources',
            'timestamp': int(time.time())
        }
        self.sheets.log_shop_transaction(tx_data)
        return {'success': True, 'message': f"Purchased {item['name']}!"} 