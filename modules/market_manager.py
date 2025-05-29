"""
Market Manager Module
Handles market listings, trades, and player transactions (per-player)
"""

import time
from typing import Dict, List, Optional
# from config.game_config import MARKET_ITEMS  # Removed unused import

class MarketManager:
    def __init__(self):
        self.listings: List[Dict] = []
        self.player_listings: Dict[str, List[Dict]] = {}
        self.last_update = time.time()

    def get_market_listings(self) -> Dict:
        return {'success': True, 'listings': self.listings}

    def add_listing(self, player_id: str, resources: Dict, price: Dict, expires_in: int = 3600) -> bool:
        listing = {
            'id': f"L{int(time.time()*1000)}",
            'seller_id': player_id,
            'resources': resources,
            'price': price,
            'expires_at': time.time() + expires_in
        }
        self.listings.append(listing)
        if player_id not in self.player_listings:
            self.player_listings[player_id] = []
        self.player_listings[player_id].append(listing)
        return True

    def get_player_listings(self, player_id: str) -> List[Dict]:
        return self.player_listings.get(player_id, [])

    def get_active_events(self):
        # Placeholder for market events
        return [] 