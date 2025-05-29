"""
Alliance Trading Manager for SkyHustle 2
Handles alliance trading, resource exchange, and trade agreements
"""

from typing import Dict, List, Optional
import time
import json
from config.alliance_config import ALLIANCE_SETTINGS
from modules.google_sheets_manager import GoogleSheetsManager

class AllianceTradingManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

    def initialize_alliance_trading(self, alliance_id: str) -> bool:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        if 'trade_offers' in alliance:
            return False
        alliance['trade_offers'] = json.dumps({})
        alliance['trade_history'] = json.dumps([])
        alliance['trade_agreements'] = json.dumps({})
        alliance['last_trade_time'] = json.dumps({})
        self.sheets.upsert_alliance(alliance)
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
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        trade_offers = json.loads(alliance['trade_offers']) if 'trade_offers' in alliance and alliance['trade_offers'] else {}
        last_trade_time = json.loads(alliance['last_trade_time']) if 'last_trade_time' in alliance and alliance['last_trade_time'] else {}
        # Check if there's already an active offer
        if target_alliance_id in trade_offers:
            return False
        # Check trade cooldown
        if target_alliance_id in last_trade_time:
            time_since_last_trade = time.time() - last_trade_time[target_alliance_id]
            if time_since_last_trade < ALLIANCE_SETTINGS['trading']['offer_cooldown']:
                return False
        # Check max active offers
        active_offers = len([offer for offer in trade_offers.values() if offer['status'] == 'pending'])
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
                
        trade_offers[target_alliance_id] = {
            'offer_resources': offer_resources,
            'request_resources': request_resources,
            'created_at': time.time(),
            'status': 'pending'
        }
        alliance['trade_offers'] = json.dumps(trade_offers)
        self.sheets.upsert_alliance(alliance)
        return True

    def accept_trade_offer(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Accept a trade offer"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        trade_offers = json.loads(alliance['trade_offers']) if 'trade_offers' in alliance and alliance['trade_offers'] else {}
        last_trade_time = json.loads(alliance['last_trade_time']) if 'last_trade_time' in alliance and alliance['last_trade_time'] else {}
        if target_alliance_id not in trade_offers:
            return False
        offer = trade_offers[target_alliance_id]
        if offer['status'] != 'pending':
            return False
        
        # Apply trade tax
        taxed_offer = self._apply_trade_tax(offer['offer_resources'])
        taxed_request = self._apply_trade_tax(offer['request_resources'])
        
        # Record the trade with taxed resources
        self._record_trade(alliance, target_alliance_id, {
            'offer_resources': taxed_offer,
            'request_resources': taxed_request
        })
        
        # Update last trade time
        last_trade_time[target_alliance_id] = time.time()
        trade_offers[target_alliance_id]['status'] = 'accepted'
        alliance['trade_offers'] = json.dumps(trade_offers)
        alliance['last_trade_time'] = json.dumps(last_trade_time)
        self.sheets.upsert_alliance(alliance)
        return True

    def reject_trade_offer(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Reject a trade offer"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        trade_offers = json.loads(alliance['trade_offers']) if 'trade_offers' in alliance and alliance['trade_offers'] else {}
        if target_alliance_id not in trade_offers:
            return False
        offer = trade_offers[target_alliance_id]
        if offer['status'] != 'pending':
            return False
        
        # Remove the offer
        del trade_offers[target_alliance_id]
        alliance['trade_offers'] = json.dumps(trade_offers)
        self.sheets.upsert_alliance(alliance)
        return True

    def create_trade_agreement(self, alliance_id: str, target_alliance_id: str, 
                             terms: Dict, duration: int) -> bool:
        """Create a long-term trade agreement between alliances"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        trade_agreements = json.loads(alliance['trade_agreements']) if 'trade_agreements' in alliance and alliance['trade_agreements'] else {}
        # Check if agreement already exists
        if target_alliance_id in trade_agreements:
            return False
            
        # Validate duration
        if (duration < ALLIANCE_SETTINGS['trading']['agreement_duration']['min'] or 
            duration > ALLIANCE_SETTINGS['trading']['agreement_duration']['max']):
            return False
            
        # Check max active agreements
        active_agreements = len([agreement for agreement in trade_agreements.values() 
                               if agreement['status'] == 'active'])
        if active_agreements >= ALLIANCE_SETTINGS['trading']['max_active_agreements']:
            return False
            
        trade_agreements[target_alliance_id] = {
            'terms': terms,
            'start_time': time.time(),
            'end_time': time.time() + duration,
            'status': 'active'
        }
        alliance['trade_agreements'] = json.dumps(trade_agreements)
        self.sheets.upsert_alliance(alliance)
        return True

    def get_trade_agreement(self, alliance_id: str, target_alliance_id: str) -> Optional[Dict]:
        """Get active trade agreement between alliances"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return None
        trade_agreements = json.loads(alliance['trade_agreements']) if 'trade_agreements' in alliance and alliance['trade_agreements'] else {}
        agreement = trade_agreements.get(target_alliance_id)
        if not agreement or agreement['status'] != 'active':
            return None
            
        # Check if agreement has expired
        if time.time() > agreement['end_time']:
            agreement['status'] = 'expired'
            alliance['trade_agreements'] = json.dumps(trade_agreements)
            self.sheets.upsert_alliance(alliance)
            return None
            
        return agreement

    def cancel_trade_agreement(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Cancel an active trade agreement"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        trade_agreements = json.loads(alliance['trade_agreements']) if 'trade_agreements' in alliance and alliance['trade_agreements'] else {}
        if target_alliance_id not in trade_agreements:
            return False
        agreement = trade_agreements[target_alliance_id]
        if agreement['status'] != 'active':
            return False
            
        agreement['status'] = 'cancelled'
        agreement['end_time'] = time.time()
        alliance['trade_agreements'] = json.dumps(trade_agreements)
        self.sheets.upsert_alliance(alliance)
        return True

    def get_active_offers(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all active trade offers for an alliance"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'trade_offers' not in alliance:
            return {}
        trade_offers = json.loads(alliance['trade_offers']) if alliance['trade_offers'] else {}
        return {k: v for k, v in trade_offers.items() if v['status'] == 'pending'}

    def get_trade_history(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        """Get recent trade history for an alliance"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'trade_history' not in alliance:
            return []
        history = json.loads(alliance['trade_history']) if alliance['trade_history'] else []
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def _record_trade(self, alliance, target_alliance_id: str, offer: Dict) -> None:
        """Record a completed trade"""
        history = json.loads(alliance['trade_history']) if 'trade_history' in alliance and alliance['trade_history'] else []
        history.append({
            'target_alliance_id': target_alliance_id,
            'offer': offer,
            'timestamp': time.time()
        })
        alliance['trade_history'] = json.dumps(history)
        self.sheets.upsert_alliance(alliance)

    def get_all_trade_agreements(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all active trade agreements for an alliance"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'trade_agreements' not in alliance:
            return {}
        return json.loads(alliance['trade_agreements']) if alliance['trade_agreements'] else {} 