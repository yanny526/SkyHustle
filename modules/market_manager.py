"""
Market Manager Module
Handles player trading, market listings, and special market events
"""

import time
from typing import Dict, List, Optional
from config.game_config import MARKET_SETTINGS, MARKET_EVENTS

class MarketManager:
    def __init__(self):
        self.listings = {}  # Store active market listings
        self.trade_history = {}  # Store trade history for each player
        self.active_events = {}  # Store active market events
        self.last_event_time = {}  # Track last event time for each player

    def create_listing(self, seller_id: str, resources: Dict, price: Dict) -> Dict:
        """Create a new market listing"""
        # Check if player has too many active listings
        if self._get_player_listings_count(seller_id) >= MARKET_SETTINGS['max_listings_per_player']:
            return {'success': False, 'message': 'Maximum number of listings reached'}

        # Generate listing ID
        listing_id = f"listing_{int(time.time())}_{seller_id}"

        # Create listing
        listing = {
            'id': listing_id,
            'seller_id': seller_id,
            'resources': resources,
            'price': price,
            'created_at': time.time(),
            'expires_at': time.time() + MARKET_SETTINGS['listing_duration']
        }

        self.listings[listing_id] = listing
        return {'success': True, 'listing': listing}

    def buy_listing(self, buyer_id: str, listing_id: str) -> Dict:
        """Buy a market listing"""
        if listing_id not in self.listings:
            return {'success': False, 'message': 'Listing not found'}

        listing = self.listings[listing_id]

        # Check if listing has expired
        if time.time() >= listing['expires_at']:
            del self.listings[listing_id]
            return {'success': False, 'message': 'Listing has expired'}

        # Check if buyer is trying to buy their own listing
        if buyer_id == listing['seller_id']:
            return {'success': False, 'message': 'Cannot buy your own listing'}

        # Record trade
        trade = {
            'listing_id': listing_id,
            'seller_id': listing['seller_id'],
            'buyer_id': buyer_id,
            'resources': listing['resources'],
            'price': listing['price'],
            'timestamp': time.time()
        }

        # Add to trade history
        for player_id in [buyer_id, listing['seller_id']]:
            if player_id not in self.trade_history:
                self.trade_history[player_id] = []
            self.trade_history[player_id].append(trade)

        # Remove listing
        del self.listings[listing_id]

        return {'success': True, 'trade': trade}

    def cancel_listing(self, seller_id: str, listing_id: str) -> Dict:
        """Cancel a market listing"""
        if listing_id not in self.listings:
            return {'success': False, 'message': 'Listing not found'}

        listing = self.listings[listing_id]

        # Check if seller owns the listing
        if seller_id != listing['seller_id']:
            return {'success': False, 'message': 'Not your listing'}

        # Remove listing
        del self.listings[listing_id]
        return {'success': True, 'message': 'Listing cancelled'}

    def get_market_listings(self, filters: Optional[Dict] = None) -> Dict:
        """Get market listings with optional filters"""
        current_time = time.time()
        active_listings = []

        # Clean up expired listings
        expired = []
        for listing_id, listing in self.listings.items():
            if current_time >= listing['expires_at']:
                expired.append(listing_id)
            else:
                active_listings.append(listing)

        # Remove expired listings
        for listing_id in expired:
            del self.listings[listing_id]

        # Apply filters if provided
        if filters:
            filtered_listings = []
            for listing in active_listings:
                matches = True
                for key, value in filters.items():
                    if key in listing and listing[key] != value:
                        matches = False
                        break
                if matches:
                    filtered_listings.append(listing)
            active_listings = filtered_listings

        return {'success': True, 'listings': active_listings}

    def get_player_listings(self, player_id: str) -> Dict:
        """Get all listings for a player"""
        listings = [
            listing for listing in self.listings.values()
            if listing['seller_id'] == player_id
        ]
        return {'success': True, 'listings': listings}

    def get_trade_history(self, player_id: str, limit: int = 10) -> Dict:
        """Get trade history for a player"""
        if player_id not in self.trade_history:
            return {'success': False, 'message': 'No trade history found'}

        history = sorted(
            self.trade_history[player_id],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]

        return {'success': True, 'history': history}

    def start_market_event(self, event_type: str) -> Dict:
        """Start a special market event"""
        if event_type not in MARKET_EVENTS:
            return {'success': False, 'message': 'Invalid event type'}

        event_info = MARKET_EVENTS[event_type]
        event_id = f"event_{int(time.time())}"

        event = {
            'id': event_id,
            'type': event_type,
            'name': event_info['name'],
            'description': event_info['description'],
            'start_time': time.time(),
            'end_time': time.time() + event_info['duration'],
            'bonus': event_info['bonus']
        }

        self.active_events[event_id] = event
        return {'success': True, 'event': event}

    def get_active_events(self) -> Dict:
        """Get all active market events"""
        current_time = time.time()
        active_events = []

        # Clean up expired events
        expired = []
        for event_id, event in self.active_events.items():
            if current_time >= event['end_time']:
                expired.append(event_id)
            else:
                active_events.append(event)

        # Remove expired events
        for event_id in expired:
            del self.active_events[event_id]

        return {'success': True, 'events': active_events}

    def _get_player_listings_count(self, player_id: str) -> int:
        """Get number of active listings for a player"""
        return len([
            listing for listing in self.listings.values()
            if listing['seller_id'] == player_id
        ]) 