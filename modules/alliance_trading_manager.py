"""
Alliance Trading Manager for SkyHustle 2
Handles alliance trading, resource exchange, and trade agreements
"""

from typing import Dict, List, Optional
import time
from config.alliance_config import ALLIANCE_SETTINGS

class AllianceTradingManager:
    def __init__(self):
        self.trade_offers: Dict[str, Dict[str, Dict]] = {}  # alliance_id -> target_alliance_id -> offer
        self.trade_history: Dict[str, List[Dict]] = {}  # alliance_id -> trade history
        self.trade_agreements: Dict[str, Dict[str, Dict]] = {}  # alliance_id -> target_alliance_id -> agreement
        self.last_trade_time: Dict[str, Dict[str, float]] = {}  # alliance_id -> target_alliance_id -> timestamp

    def initialize_alliance_trading(self, alliance_id: str) -> bool:
        """Initialize trading system for a new alliance"""
        if alliance_id in self.trade_offers:
            return False
            
        self.trade_offers[alliance_id] = {}
        self.trade_history[alliance_id] = []
        self.trade_agreements[alliance_id] = {}
        self.last_trade_time[alliance_id] = {}
        return True

    def _validate_trade_resources(self, resources: Dict[str, int]) -> bool:
        """Validate resource quantities against restrictions"""
        for resource, quantity in resources.items():
            if resource in ALLIANCE_SETTINGS['trading']['resource_restrictions']['restricted_resources']:
                max_quantity = ALLIANCE_SETTINGS['trading']['resource_restrictions']['max_quantity'].get(resource, 0)
                if quantity > max_quantity:
                    return False
        return True

    def _calculate_trade_value(self, resources: Dict[str, int]) -> int:
        """Calculate the total value of resources in a trade"""
        # This is a placeholder - in a real implementation, you would have resource values
        return sum(resources.values())

    def _apply_trade_tax(self, resources: Dict[str, int]) -> Dict[str, int]:
        """Apply trade tax to resources"""
        tax_rate = ALLIANCE_SETTINGS['trading']['trade_tax_rate']
        taxed_resources = {}
        for resource, quantity in resources.items():
            tax_amount = int(quantity * tax_rate)
            taxed_resources[resource] = quantity - tax_amount
        return taxed_resources

    def create_trade_offer(self, alliance_id: str, target_alliance_id: str, 
                          offer_resources: Dict[str, int], request_resources: Dict[str, int]) -> bool:
        """Create a new trade offer between alliances"""
        if alliance_id not in self.trade_offers:
            return False
            
        # Check if there's already an active offer
        if target_alliance_id in self.trade_offers[alliance_id]:
            return False
            
        # Check trade cooldown
        if target_alliance_id in self.last_trade_time[alliance_id]:
            time_since_last_trade = time.time() - self.last_trade_time[alliance_id][target_alliance_id]
            if time_since_last_trade < ALLIANCE_SETTINGS['trading']['offer_cooldown']:
                return False

        # Check max active offers
        active_offers = len([offer for offer in self.trade_offers[alliance_id].values() 
                           if offer['status'] == 'pending'])
        if active_offers >= ALLIANCE_SETTINGS['trading']['max_active_offers']:
            return False

        # Validate resource quantities
        if not self._validate_trade_resources(offer_resources) or not self._validate_trade_resources(request_resources):
            return False

        # Validate trade value
        offer_value = self._calculate_trade_value(offer_resources)
        request_value = self._calculate_trade_value(request_resources)
        
        if (offer_value < ALLIANCE_SETTINGS['trading']['min_trade_value'] or 
            offer_value > ALLIANCE_SETTINGS['trading']['max_trade_value'] or
            request_value < ALLIANCE_SETTINGS['trading']['min_trade_value'] or
            request_value > ALLIANCE_SETTINGS['trading']['max_trade_value']):
            return False
                
        self.trade_offers[alliance_id][target_alliance_id] = {
            'offer_resources': offer_resources,
            'request_resources': request_resources,
            'created_at': time.time(),
            'status': 'pending'
        }
        return True

    def accept_trade_offer(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Accept a trade offer"""
        if alliance_id not in self.trade_offers or target_alliance_id not in self.trade_offers[alliance_id]:
            return False
            
        offer = self.trade_offers[alliance_id][target_alliance_id]
        if offer['status'] != 'pending':
            return False
            
        # Apply trade tax
        taxed_offer = self._apply_trade_tax(offer['offer_resources'])
        taxed_request = self._apply_trade_tax(offer['request_resources'])
        
        # Record the trade with taxed resources
        self._record_trade(alliance_id, target_alliance_id, {
            'offer_resources': taxed_offer,
            'request_resources': taxed_request
        })
        
        # Update last trade time
        self.last_trade_time[alliance_id][target_alliance_id] = time.time()
        self.last_trade_time[target_alliance_id][alliance_id] = time.time()
        
        # Remove the offer
        del self.trade_offers[alliance_id][target_alliance_id]
        return True

    def reject_trade_offer(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Reject a trade offer"""
        if alliance_id not in self.trade_offers or target_alliance_id not in self.trade_offers[alliance_id]:
            return False
            
        offer = self.trade_offers[alliance_id][target_alliance_id]
        if offer['status'] != 'pending':
            return False
            
        # Remove the offer
        del self.trade_offers[alliance_id][target_alliance_id]
        return True

    def create_trade_agreement(self, alliance_id: str, target_alliance_id: str, 
                             terms: Dict, duration: int) -> bool:
        """Create a long-term trade agreement between alliances"""
        if alliance_id not in self.trade_agreements:
            return False
            
        # Check if agreement already exists
        if target_alliance_id in self.trade_agreements[alliance_id]:
            return False
            
        # Validate duration
        if (duration < ALLIANCE_SETTINGS['trading']['agreement_duration']['min'] or 
            duration > ALLIANCE_SETTINGS['trading']['agreement_duration']['max']):
            return False
            
        # Check max active agreements
        active_agreements = len([agreement for agreement in self.trade_agreements[alliance_id].values() 
                               if agreement['status'] == 'active'])
        if active_agreements >= ALLIANCE_SETTINGS['trading']['max_active_agreements']:
            return False
            
        self.trade_agreements[alliance_id][target_alliance_id] = {
            'terms': terms,
            'start_time': time.time(),
            'end_time': time.time() + duration,
            'status': 'active'
        }
        return True

    def get_trade_agreement(self, alliance_id: str, target_alliance_id: str) -> Optional[Dict]:
        """Get active trade agreement between alliances"""
        if alliance_id not in self.trade_agreements:
            return None
            
        agreement = self.trade_agreements[alliance_id].get(target_alliance_id)
        if not agreement or agreement['status'] != 'active':
            return None
            
        # Check if agreement has expired
        if time.time() > agreement['end_time']:
            agreement['status'] = 'expired'
            return None
            
        return agreement

    def cancel_trade_agreement(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Cancel an active trade agreement"""
        if alliance_id not in self.trade_agreements:
            return False
            
        if target_alliance_id not in self.trade_agreements[alliance_id]:
            return False
            
        agreement = self.trade_agreements[alliance_id][target_alliance_id]
        if agreement['status'] != 'active':
            return False
            
        agreement['status'] = 'cancelled'
        agreement['end_time'] = time.time()
        return True

    def get_active_offers(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all active trade offers for an alliance"""
        if alliance_id not in self.trade_offers:
            return {}
            
        active_offers = {}
        for target_id, offer in self.trade_offers[alliance_id].items():
            if offer['status'] == 'pending':
                active_offers[target_id] = offer
                
        return active_offers

    def get_trade_history(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        """Get recent trade history for an alliance"""
        if alliance_id not in self.trade_history:
            return []
            
        return sorted(
            self.trade_history[alliance_id],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]

    def _record_trade(self, alliance_id: str, target_alliance_id: str, offer: Dict) -> None:
        """Record a completed trade"""
        if alliance_id not in self.trade_history:
            self.trade_history[alliance_id] = []
            
        self.trade_history[alliance_id].append({
            'target_alliance': target_alliance_id,
            'offer_resources': offer['offer_resources'],
            'request_resources': offer['request_resources'],
            'timestamp': time.time()
        })

    def get_all_trade_agreements(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all active trade agreements for an alliance"""
        if alliance_id not in self.trade_agreements:
            return {}
            
        active_agreements = {}
        for target_id, agreement in self.trade_agreements[alliance_id].items():
            if agreement['status'] == 'active' and time.time() <= agreement['end_time']:
                active_agreements[target_id] = agreement
                
        return active_agreements 