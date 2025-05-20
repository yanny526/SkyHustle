"""
Alliance Diplomacy Manager for SkyHustle 2
Handles alliance diplomatic relationships, treaties, and coordination
"""

from typing import Dict, List, Optional
import time
from config.alliance_config import ALLIANCE_SETTINGS

class AllianceDiplomacyManager:
    def __init__(self):
        self.relationships: Dict[str, Dict[str, Dict]] = {}  # alliance_id -> target_alliance_id -> relationship
        self.treaties: Dict[str, Dict[str, Dict]] = {}  # alliance_id -> target_alliance_id -> treaty
        self.diplomatic_actions: Dict[str, List[Dict]] = {}  # alliance_id -> action history
        self.peace_treaties: Dict[str, Dict[str, Dict]] = {}  # alliance_id -> target_alliance_id -> peace treaty
        self.last_diplomatic_action: Dict[str, Dict[str, float]] = {}  # alliance_id -> {action_type: timestamp}

    def initialize_alliance_diplomacy(self, alliance_id: str) -> bool:
        """Initialize diplomacy system for a new alliance"""
        if alliance_id in self.relationships:
            return False
            
        self.relationships[alliance_id] = {}
        self.treaties[alliance_id] = {}
        self.diplomatic_actions[alliance_id] = []
        self.peace_treaties[alliance_id] = {}
        return True

    def get_relationship(self, alliance_id: str, target_alliance_id: str) -> Dict:
        """Get diplomatic relationship between two alliances"""
        if alliance_id not in self.relationships:
            return {'status': 'neutral', 'points': 0}
            
        return self.relationships[alliance_id].get(target_alliance_id, {'status': 'neutral', 'points': 0})

    def update_relationship(self, alliance_id: str, target_alliance_id: str, points: int) -> bool:
        """Update diplomatic relationship points"""
        if alliance_id not in self.relationships:
            return False
            
        if target_alliance_id not in self.relationships[alliance_id]:
            self.relationships[alliance_id][target_alliance_id] = {'status': 'neutral', 'points': 0}
            
        self.relationships[alliance_id][target_alliance_id]['points'] += points
        
        # Update relationship status based on points
        points = self.relationships[alliance_id][target_alliance_id]['points']
        if points >= ALLIANCE_SETTINGS['diplomacy']['allied_threshold']:
            status = 'allied'
        elif points >= ALLIANCE_SETTINGS['diplomacy']['friendly_threshold']:
            status = 'friendly'
        elif points <= ALLIANCE_SETTINGS['diplomacy']['hostile_threshold']:
            status = 'hostile'
        else:
            status = 'neutral'
            
        self.relationships[alliance_id][target_alliance_id]['status'] = status
        return True

    def create_treaty(self, alliance_id: str, target_alliance_id: str, treaty_type: str, 
                     duration: int, terms: Dict) -> bool:
        """Create a new treaty between alliances"""
        if alliance_id not in self.treaties:
            return False
            
        if treaty_type not in ALLIANCE_SETTINGS['diplomacy']['treaty_types']:
            return False
            
        # Check if treaty already exists
        if target_alliance_id in self.treaties[alliance_id]:
            return False

        # Validate treaty duration
        treaty_info = ALLIANCE_SETTINGS['diplomacy']['treaty_types'][treaty_type]
        if duration < treaty_info['duration'] * 0.5 or duration > treaty_info['duration'] * 1.5:
            return False

        # Check diplomatic action cooldown
        current_time = time.time()
        if alliance_id in self.last_diplomatic_action:
            last_action = self.last_diplomatic_action[alliance_id].get('create_treaty', 0)
            if current_time - last_action < ALLIANCE_SETTINGS['diplomacy']['diplomatic_actions']['trade_agreement']['cooldown']:
                return False
            
        self.treaties[alliance_id][target_alliance_id] = {
            'type': treaty_type,
            'start_time': current_time,
            'end_time': current_time + duration,
            'terms': terms,
            'status': 'active'
        }
        
        # Update last diplomatic action time
        if alliance_id not in self.last_diplomatic_action:
            self.last_diplomatic_action[alliance_id] = {}
        self.last_diplomatic_action[alliance_id]['create_treaty'] = current_time
        
        # Record diplomatic action
        self._record_diplomatic_action(alliance_id, 'create_treaty', {
            'target_alliance': target_alliance_id,
            'treaty_type': treaty_type,
            'duration': duration
        })
        
        return True

    def get_treaty(self, alliance_id: str, target_alliance_id: str) -> Optional[Dict]:
        """Get active treaty between alliances"""
        if alliance_id not in self.treaties:
            return None
            
        treaty = self.treaties[alliance_id].get(target_alliance_id)
        if not treaty or treaty['status'] != 'active':
            return None
            
        # Check if treaty has expired
        if time.time() > treaty['end_time']:
            treaty['status'] = 'expired'
            return None
            
        return treaty

    def cancel_treaty(self, alliance_id: str, target_alliance_id: str) -> bool:
        """Cancel an active treaty"""
        if alliance_id not in self.treaties:
            return False
            
        if target_alliance_id not in self.treaties[alliance_id]:
            return False
            
        treaty = self.treaties[alliance_id][target_alliance_id]
        if treaty['status'] != 'active':
            return False
            
        treaty['status'] = 'cancelled'
        treaty['end_time'] = time.time()
        
        # Record diplomatic action
        self._record_diplomatic_action(alliance_id, 'cancel_treaty', {
            'target_alliance': target_alliance_id,
            'treaty_type': treaty['type']
        })
        
        return True

    def create_peace_treaty(self, alliance_id: str, target_alliance_id: str, 
                          duration: int, terms: Dict) -> bool:
        """Create a peace treaty between alliances"""
        if alliance_id not in self.peace_treaties:
            return False
            
        # Check if peace treaty already exists
        if target_alliance_id in self.peace_treaties[alliance_id]:
            return False

        # Validate peace treaty duration
        if (duration < ALLIANCE_SETTINGS['diplomacy']['peace_treaty']['min_duration'] or 
            duration > ALLIANCE_SETTINGS['diplomacy']['peace_treaty']['max_duration']):
            return False

        # Check diplomatic action cooldown
        current_time = time.time()
        if alliance_id in self.last_diplomatic_action:
            last_action = self.last_diplomatic_action[alliance_id].get('create_peace_treaty', 0)
            if current_time - last_action < ALLIANCE_SETTINGS['diplomacy']['diplomatic_actions']['trade_agreement']['cooldown']:
                return False
            
        self.peace_treaties[alliance_id][target_alliance_id] = {
            'start_time': current_time,
            'end_time': current_time + duration,
            'terms': terms,
            'status': 'active'
        }
        
        # Update last diplomatic action time
        if alliance_id not in self.last_diplomatic_action:
            self.last_diplomatic_action[alliance_id] = {}
        self.last_diplomatic_action[alliance_id]['create_peace_treaty'] = current_time
        
        # Record diplomatic action
        self._record_diplomatic_action(alliance_id, 'create_peace_treaty', {
            'target_alliance': target_alliance_id,
            'duration': duration
        })
        
        return True

    def get_peace_treaty(self, alliance_id: str, target_alliance_id: str) -> Optional[Dict]:
        """Get active peace treaty between alliances"""
        if alliance_id not in self.peace_treaties:
            return None
            
        treaty = self.peace_treaties[alliance_id].get(target_alliance_id)
        if not treaty or treaty['status'] != 'active':
            return None
            
        # Check if treaty has expired
        if time.time() > treaty['end_time']:
            treaty['status'] = 'expired'
            return None
            
        return treaty

    def get_diplomatic_actions(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        """Get recent diplomatic actions for an alliance"""
        if alliance_id not in self.diplomatic_actions:
            return []
            
        return sorted(
            self.diplomatic_actions[alliance_id],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]

    def _record_diplomatic_action(self, alliance_id: str, action_type: str, details: Dict) -> None:
        """Record a diplomatic action"""
        if alliance_id not in self.diplomatic_actions:
            self.diplomatic_actions[alliance_id] = []
            
        self.diplomatic_actions[alliance_id].append({
            'type': action_type,
            'timestamp': time.time(),
            'details': details
        })

    def get_all_relationships(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all diplomatic relationships for an alliance"""
        if alliance_id not in self.relationships:
            return {}
            
        return self.relationships[alliance_id]

    def get_all_treaties(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all active treaties for an alliance"""
        if alliance_id not in self.treaties:
            return {}
            
        active_treaties = {}
        for target_id, treaty in self.treaties[alliance_id].items():
            if treaty['status'] == 'active' and time.time() <= treaty['end_time']:
                active_treaties[target_id] = treaty
                
        return active_treaties

    def get_all_peace_treaties(self, alliance_id: str) -> Dict[str, Dict]:
        """Get all active peace treaties for an alliance"""
        if alliance_id not in self.peace_treaties:
            return {}
            
        active_treaties = {}
        for target_id, treaty in self.peace_treaties[alliance_id].items():
            if treaty['status'] == 'active' and time.time() <= treaty['end_time']:
                active_treaties[target_id] = treaty
                
        return active_treaties 