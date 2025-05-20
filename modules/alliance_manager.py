"""
Alliance Manager for SkyHustle 2
Handles alliance creation, management, and interactions
"""

import time
from typing import Dict, List, Optional
from config.game_config import ALLIANCE_SETTINGS

class AllianceManager:
    def __init__(self):
        self.alliances: Dict[str, Dict] = {}  # alliance_id -> alliance data
        self.members: Dict[str, str] = {}  # player_id -> alliance_id
        self.join_requests: Dict[str, List[str]] = {}  # alliance_id -> [player_id]
        self.wars: Dict[str, Dict] = {}  # war_id -> war data
        self.chat_history: Dict[str, List[Dict]] = {}  # alliance_id -> [message]
        self.resources: Dict[str, Dict[str, int]] = {}  # alliance_id -> {resource_id: amount}
        self.levels: Dict[str, int] = {}  # alliance_id -> level
        self.xp: Dict[str, int] = {}  # alliance_id -> xp
        self.last_resource_update: Dict[str, float] = {}  # alliance_id -> last update time

    def create_alliance(self, leader_id: str, name: str, description: str) -> Dict:
        """Create a new alliance"""
        # Check if player is already in an alliance
        if leader_id in self.members:
            return {'success': False, 'message': 'You are already in an alliance!'}
        
        # Check if name is taken
        if any(a['name'] == name for a in self.alliances.values()):
            return {'success': False, 'message': 'Alliance name is already taken!'}
        
        # Create alliance
        alliance_id = f"alliance_{len(self.alliances) + 1}"
        self.alliances[alliance_id] = {
            'id': alliance_id,
            'name': name,
            'description': description,
            'leader_id': leader_id,
            'officers': [],
            'members': [leader_id],
            'created_at': time.time(),
            'level': 1,
            'xp': 0
        }
        
        # Add leader to members
        self.members[leader_id] = alliance_id
        
        # Initialize alliance resources
        self.resources[alliance_id] = {
            'wood': 0,
            'stone': 0,
            'gold': 0,
            'food': 0
        }
        
        return {'success': True, 'alliance_id': alliance_id}

    def join_alliance(self, player_id: str, alliance_id: str) -> Dict:
        """Send a join request to an alliance"""
        # Check if player is already in an alliance
        if player_id in self.members:
            return {'success': False, 'message': 'You are already in an alliance!'}
        
        # Check if alliance exists
        if alliance_id not in self.alliances:
            return {'success': False, 'message': 'Alliance not found!'}
        
        # Check if alliance is full
        alliance = self.alliances[alliance_id]
        if len(alliance['members']) >= ALLIANCE_SETTINGS['max_members']:
            return {'success': False, 'message': 'Alliance is full!'}
        
        # Add join request
        if alliance_id not in self.join_requests:
            self.join_requests[alliance_id] = []
        self.join_requests[alliance_id].append(player_id)
        
        return {'success': True}

    def accept_join_request(self, alliance_id: str, player_id: str, acceptor_id: str) -> Dict:
        """Accept a join request"""
        # Check if acceptor has permission
        alliance = self.alliances[alliance_id]
        if acceptor_id != alliance['leader_id'] and acceptor_id not in alliance['officers']:
            return {'success': False, 'message': 'You do not have permission to accept join requests!'}
        
        # Check if request exists
        if alliance_id not in self.join_requests or player_id not in self.join_requests[alliance_id]:
            return {'success': False, 'message': 'Join request not found!'}
        
        # Add player to alliance
        alliance['members'].append(player_id)
        self.members[player_id] = alliance_id
        
        # Remove request
        self.join_requests[alliance_id].remove(player_id)
        
        return {'success': True}

    def leave_alliance(self, player_id: str) -> Dict:
        """Leave an alliance"""
        # Check if player is in an alliance
        if player_id not in self.members:
            return {'success': False, 'message': 'You are not in an alliance!'}
        
        alliance_id = self.members[player_id]
        alliance = self.alliances[alliance_id]
        
        # Check if player is leader
        if player_id == alliance['leader_id']:
            return {'success': False, 'message': 'Leader cannot leave alliance! Transfer leadership first.'}
        
        # Remove player from alliance
        alliance['members'].remove(player_id)
        if player_id in alliance['officers']:
            alliance['officers'].remove(player_id)
        
        del self.members[player_id]
        
        return {'success': True}

    def transfer_leadership(self, current_leader_id: str, new_leader_id: str) -> Dict:
        """Transfer alliance leadership"""
        # Check if current leader is in an alliance
        if current_leader_id not in self.members:
            return {'success': False, 'message': 'You are not in an alliance!'}
        
        alliance_id = self.members[current_leader_id]
        alliance = self.alliances[alliance_id]
        
        # Check if current leader is actually the leader
        if current_leader_id != alliance['leader_id']:
            return {'success': False, 'message': 'You are not the alliance leader!'}
        
        # Check if new leader is in the alliance
        if new_leader_id not in alliance['members']:
            return {'success': False, 'message': 'New leader must be a member of the alliance!'}
        
        # Transfer leadership
        alliance['leader_id'] = new_leader_id
        if new_leader_id in alliance['officers']:
            alliance['officers'].remove(new_leader_id)
        
        return {'success': True}

    def promote_to_officer(self, leader_id: str, player_id: str) -> Dict:
        """Promote a member to officer"""
        # Check if leader is in an alliance
        if leader_id not in self.members:
            return {'success': False, 'message': 'You are not in an alliance!'}
        
        alliance_id = self.members[leader_id]
        alliance = self.alliances[alliance_id]
        
        # Check if leader is actually the leader
        if leader_id != alliance['leader_id']:
            return {'success': False, 'message': 'Only the leader can promote officers!'}
        
        # Check if player is in the alliance
        if player_id not in alliance['members']:
            return {'success': False, 'message': 'Player is not in the alliance!'}
        
        # Promote to officer
        if player_id not in alliance['officers']:
            alliance['officers'].append(player_id)
        
        return {'success': True}

    def demote_officer(self, leader_id: str, player_id: str) -> Dict:
        """Demote an officer to regular member"""
        # Check if leader is in an alliance
        if leader_id not in self.members:
            return {'success': False, 'message': 'You are not in an alliance!'}
        
        alliance_id = self.members[leader_id]
        alliance = self.alliances[alliance_id]
        
        # Check if leader is actually the leader
        if leader_id != alliance['leader_id']:
            return {'success': False, 'message': 'Only the leader can demote officers!'}
        
        # Check if player is an officer
        if player_id not in alliance['officers']:
            return {'success': False, 'message': 'Player is not an officer!'}
        
        # Demote officer
        alliance['officers'].remove(player_id)
        
        return {'success': True}

    def donate_resources(self, player_id: str, alliance_id: str, resources: Dict[str, int]) -> Dict:
        """Donate resources to alliance"""
        try:
            # Check if player is in the alliance
            if player_id not in self.members or self.members[player_id] != alliance_id:
                return {'success': False, 'message': 'You are not a member of this alliance!'}
            
            # Check donation cooldown
            current_time = time.time()
            if alliance_id in self.last_resource_update:
                time_since_last = current_time - self.last_resource_update[alliance_id]
                if time_since_last < ALLIANCE_SETTINGS['donation_cooldown']:
                    return {'success': False, 'message': 'Donation cooldown active!'}
            
            # Validate resource amounts
            for resource, amount in resources.items():
                if amount <= 0:
                    return {'success': False, 'message': 'Invalid resource amount!'}
                if amount > ALLIANCE_SETTINGS['max_daily_donation']:
                    return {'success': False, 'message': 'Exceeds maximum daily donation!'}
            
            # Add resources to alliance
            for resource_id, amount in resources.items():
                if resource_id not in self.resources[alliance_id]:
                    self.resources[alliance_id][resource_id] = 0
                self.resources[alliance_id][resource_id] += amount
            
            # Update last resource update time
            self.last_resource_update[alliance_id] = current_time
            
            # Add XP to alliance
            total_donation = sum(resources.values())
            self.xp[alliance_id] = self.xp.get(alliance_id, 0) + total_donation
            
            # Check for level up
            self._check_level_up(alliance_id)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': f'Error during resource donation: {str(e)}'}

    def get_alliance_info(self, alliance_id: str) -> Dict:
        """Get alliance information"""
        if alliance_id not in self.alliances:
            return {'success': False, 'message': 'Alliance not found!'}
        
        alliance = self.alliances[alliance_id]
        return {
            'success': True,
            'alliance': {
                'id': alliance['id'],
                'name': alliance['name'],
                'description': alliance['description'],
                'leader_id': alliance['leader_id'],
                'officers': alliance['officers'],
                'members': alliance['members'],
                'created_at': alliance['created_at'],
                'level': alliance['level'],
                'xp': self.xp.get(alliance_id, 0),
                'resources': self.resources.get(alliance_id, {})
            }
        }

    def get_player_alliance(self, player_id: str) -> Optional[Dict]:
        """Get player's alliance information"""
        if player_id not in self.members:
            return None
        
        alliance_id = self.members[player_id]
        return self.get_alliance_info(alliance_id)

    def get_alliance_rankings(self) -> List[Dict]:
        """Get alliance rankings"""
        rankings = []
        for alliance_id, alliance in self.alliances.items():
            rankings.append({
                'id': alliance_id,
                'name': alliance['name'],
                'level': alliance['level'],
                'xp': self.xp.get(alliance_id, 0),
                'member_count': len(alliance['members'])
            })
        
        # Sort by level and XP
        rankings.sort(key=lambda x: (x['level'], x['xp']), reverse=True)
        return rankings

    def add_chat_message(self, alliance_id: str, player_id: str, message: str) -> Dict:
        """Add a message to alliance chat"""
        # Check if player is in the alliance
        if player_id not in self.members or self.members[player_id] != alliance_id:
            return {'success': False, 'message': 'You are not a member of this alliance!'}
        
        # Add message to chat history
        if alliance_id not in self.chat_history:
            self.chat_history[alliance_id] = []
        
        self.chat_history[alliance_id].append({
            'player_id': player_id,
            'message': message,
            'timestamp': time.time()
        })
        
        # Keep only last 100 messages
        if len(self.chat_history[alliance_id]) > 100:
            self.chat_history[alliance_id] = self.chat_history[alliance_id][-100:]
        
        return {'success': True}

    def get_chat_history(self, alliance_id: str) -> List[Dict]:
        """Get alliance chat history"""
        return self.chat_history.get(alliance_id, [])

    def declare_war(self, alliance_id: str, target_alliance_id: str, declarer_id: str) -> Dict:
        """Declare war on another alliance"""
        # Check if declarer has permission
        alliance = self.alliances[alliance_id]
        if declarer_id != alliance['leader_id'] and declarer_id not in alliance['officers']:
            return {'success': False, 'message': 'You do not have permission to declare war!'}
        
        # Check if target alliance exists
        if target_alliance_id not in self.alliances:
            return {'success': False, 'message': 'Target alliance not found!'}
        
        # Check if already at war
        for war in self.wars.values():
            if (war['alliance1_id'] == alliance_id and war['alliance2_id'] == target_alliance_id) or \
               (war['alliance1_id'] == target_alliance_id and war['alliance2_id'] == alliance_id):
                return {'success': False, 'message': 'Already at war with this alliance!'}
        
        # Create war
        war_id = f"war_{len(self.wars) + 1}"
        self.wars[war_id] = {
            'id': war_id,
            'alliance1_id': alliance_id,
            'alliance2_id': target_alliance_id,
            'start_time': time.time(),
            'end_time': time.time() + ALLIANCE_SETTINGS['war_duration'],
            'score': {alliance_id: 0, target_alliance_id: 0}
        }
        
        return {'success': True, 'war': self.wars[war_id]}

    def _check_level_up(self, alliance_id: str):
        """Check if alliance can level up"""
        current_level = self.alliances[alliance_id]['level']
        current_xp = self.xp.get(alliance_id, 0)
        required_xp = current_level * ALLIANCE_SETTINGS['xp_per_level']
        
        if current_xp >= required_xp:
            self.alliances[alliance_id]['level'] += 1
            self.xp[alliance_id] = current_xp - required_xp 