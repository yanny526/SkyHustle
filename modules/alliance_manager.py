"""
Alliance Manager for SkyHustle 2
Handles alliance creation, management, and interactions
"""

import time
import json
from typing import Dict, List, Optional
from config.game_config import ALLIANCE_SETTINGS
from modules.google_sheets_manager import GoogleSheetsManager

class AllianceManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

    def create_alliance(self, leader_id: str, name: str, description: str) -> Dict:
        """Create a new alliance"""
        # Check if player is already in an alliance
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if leader_id in members:
                return {'success': False, 'message': 'You are already in an alliance!'}
        
        # Check if name is taken
        if any(a['name'] == name for a in self.sheets.get_all_alliances()):
            return {'success': False, 'message': 'Alliance name is already taken!'}
        
        # Create alliance
        alliance_id = f"alliance_{int(time.time())}"
        alliance_data = {
            'alliance_id': alliance_id,
            'name': name,
            'level': 1,
            'xp': 0,
            'members': json.dumps([leader_id]),
            'leader': leader_id,
            'created_at': time.time(),
            'perks': json.dumps([]),
            'war_history': json.dumps([]),
            'diplomacy': json.dumps([]),
            'resources': json.dumps({'wood': 0, 'stone': 0, 'gold': 0, 'food': 0})
        }
        self.sheets.upsert_alliance(alliance_data)
        return {'success': True, 'alliance_id': alliance_id}

    def join_alliance(self, player_id: str, alliance_id: str) -> Dict:
        """Send a join request to an alliance"""
        # Check if player is already in an alliance
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if player_id in members:
                return {'success': False, 'message': 'You are already in an alliance!'}
        
        # Check if alliance exists
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return {'success': False, 'message': 'Alliance not found!'}
        
        members = json.loads(alliance['members']) if alliance['members'] else []
        if len(members) >= ALLIANCE_SETTINGS['max_members']:
            return {'success': False, 'message': 'Alliance is full!'}
        
        members.append(player_id)
        alliance['members'] = json.dumps(members)
        self.sheets.upsert_alliance(alliance)
        return {'success': True}

    def accept_join_request(self, alliance_id: str, player_id: str, acceptor_id: str) -> Dict:
        """Accept a join request"""
        # Check if acceptor has permission
        alliance = self.sheets.get_alliance(alliance_id)
        if acceptor_id != alliance['leader'] and acceptor_id not in json.loads(alliance['officers']) if alliance['officers'] else []:
            return {'success': False, 'message': 'You do not have permission to accept join requests!'}
        
        # Check if request exists
        members = json.loads(alliance['members']) if alliance['members'] else []
        if player_id not in members:
            return {'success': False, 'message': 'Join request not found!'}
        
        # Add player to alliance
        members.append(player_id)
        alliance['members'] = json.dumps(members)
        self.sheets.upsert_alliance(alliance)
        
        return {'success': True}

    def leave_alliance(self, player_id: str) -> Dict:
        """Leave an alliance"""
        # Find the alliance the player is in
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if player_id in members:
                if player_id == alliance['leader']:
                    return {'success': False, 'message': 'Leader cannot leave alliance! Transfer leadership first.'}
                members.remove(player_id)
                alliance['members'] = json.dumps(members)
                self.sheets.upsert_alliance(alliance)
                return {'success': True}
        return {'success': False, 'message': 'You are not in an alliance!'}

    def transfer_leadership(self, current_leader_id: str, new_leader_id: str) -> Dict:
        """Transfer alliance leadership"""
        # Check if current leader is in an alliance
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if current_leader_id in members:
                if current_leader_id != alliance['leader']:
                    return {'success': False, 'message': 'You are not the alliance leader!'}
                
                # Check if new leader is in the alliance
                if new_leader_id not in members:
                    return {'success': False, 'message': 'New leader must be a member of the alliance!'}
                
                # Transfer leadership
                members.remove(current_leader_id)
                members.append(new_leader_id)
                alliance['leader'] = new_leader_id
                alliance['members'] = json.dumps(members)
                self.sheets.upsert_alliance(alliance)
                return {'success': True}
        return {'success': False, 'message': 'You are not in an alliance!'}

    def promote_to_officer(self, leader_id: str, player_id: str) -> Dict:
        """Promote a member to officer"""
        # Check if leader is in an alliance
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if leader_id in members:
                if leader_id != alliance['leader']:
                    return {'success': False, 'message': 'Only the leader can promote officers!'}
                
                # Check if player is in the alliance
                if player_id not in members:
                    return {'success': False, 'message': 'Player is not in the alliance!'}
                
                # Promote to officer
                if player_id not in json.loads(alliance['officers']) if alliance['officers'] else []:
                    json.loads(alliance['officers']).append(player_id)
                    alliance['officers'] = json.dumps(json.loads(alliance['officers']))
                self.sheets.upsert_alliance(alliance)
                return {'success': True}
        return {'success': False, 'message': 'You are not in an alliance!'}

    def demote_officer(self, leader_id: str, player_id: str) -> Dict:
        """Demote an officer to regular member"""
        # Check if leader is in an alliance
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if leader_id in members:
                if leader_id != alliance['leader']:
                    return {'success': False, 'message': 'Only the leader can demote officers!'}
                
                # Check if player is an officer
                if player_id not in json.loads(alliance['officers']) if alliance['officers'] else []:
                    json.loads(alliance['officers']).remove(player_id)
                    alliance['officers'] = json.dumps(json.loads(alliance['officers']))
                self.sheets.upsert_alliance(alliance)
                return {'success': True}
        return {'success': False, 'message': 'You are not in an alliance!'}

    def donate_resources(self, player_id: str, alliance_id: str, resources: Dict[str, int]) -> Dict:
        """Donate resources to alliance"""
        try:
            # Check if player is in the alliance
            for alliance in self.sheets.get_all_alliances():
                members = json.loads(alliance['members']) if alliance['members'] else []
                if player_id in members and alliance['alliance_id'] == alliance_id:
                    # Check donation cooldown
                    current_time = time.time()
                    if 'last_resource_update' in alliance:
                        time_since_last = current_time - float(alliance['last_resource_update'])
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
                        if resource_id not in json.loads(alliance['resources']) if alliance['resources'] else {}:
                            json.loads(alliance['resources'])[resource_id] = json.loads(alliance['resources']).get(resource_id, 0) + amount
                    
                    # Update last resource update time
                    alliance['last_resource_update'] = current_time
                    
                    # Add XP to alliance
                    total_donation = sum(resources.values())
                    if 'xp' in alliance:
                        alliance['xp'] = float(alliance['xp']) + total_donation
                    else:
                        alliance['xp'] = total_donation
                    
                    # Check for level up
                    self._check_level_up(alliance['alliance_id'])
                    
                    self.sheets.upsert_alliance(alliance)
                    return {'success': True}
            return {'success': False, 'message': 'You are not a member of this alliance!'}
        except Exception as e:
            return {'success': False, 'message': f'Error during resource donation: {str(e)}'}

    def get_alliance_info(self, alliance_id: str) -> Dict:
        """Get alliance information"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return {'success': False, 'message': 'Alliance not found!'}
        
        # Decode JSON fields
        alliance['members'] = json.loads(alliance['members']) if alliance['members'] else []
        alliance['perks'] = json.loads(alliance['perks']) if alliance['perks'] else []
        alliance['war_history'] = json.loads(alliance['war_history']) if alliance['war_history'] else []
        alliance['diplomacy'] = json.loads(alliance['diplomacy']) if alliance['diplomacy'] else []
        alliance['resources'] = json.loads(alliance['resources']) if alliance['resources'] else {}
        return {'success': True, 'alliance': alliance}

    def get_player_alliance(self, player_id: str) -> Optional[Dict]:
        """Get player's alliance information"""
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if player_id in members:
                return self.get_alliance_info(alliance['alliance_id'])
        return None

    def get_alliance_rankings(self) -> List[Dict]:
        """Get alliance rankings"""
        rankings = []
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            rankings.append({
                'id': alliance['alliance_id'],
                'name': alliance['name'],
                'level': float(alliance['level']),
                'xp': float(alliance['xp']),
                'member_count': len(members)
            })
        
        # Sort by level and XP
        rankings.sort(key=lambda x: (x['level'], x['xp']), reverse=True)
        return rankings

    def add_chat_message(self, alliance_id: str, player_id: str, message: str) -> Dict:
        """Add a message to alliance chat"""
        # Check if player is in the alliance
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if player_id in members and alliance['alliance_id'] == alliance_id:
                # Add message to chat history
                if 'chat_history' not in alliance:
                    alliance['chat_history'] = []
                
                alliance['chat_history'].append({
                    'player_id': player_id,
                    'message': message,
                    'timestamp': time.time()
                })
                
                # Keep only last 100 messages
                if len(alliance['chat_history']) > 100:
                    alliance['chat_history'] = alliance['chat_history'][-100:]
                
                self.sheets.upsert_alliance(alliance)
                return {'success': True}
        return {'success': False, 'message': 'You are not a member of this alliance!'}

    def get_chat_history(self, alliance_id: str) -> List[Dict]:
        """Get alliance chat history"""
        for alliance in self.sheets.get_all_alliances():
            if alliance['alliance_id'] == alliance_id and 'chat_history' in alliance:
                return alliance['chat_history']
        return []

    def declare_war(self, alliance_id: str, target_alliance_id: str, declarer_id: str) -> Dict:
        """Declare war on another alliance"""
        # Check if declarer has permission
        for alliance in self.sheets.get_all_alliances():
            members = json.loads(alliance['members']) if alliance['members'] else []
            if declarer_id in members:
                if declarer_id != alliance['leader']:
                    return {'success': False, 'message': 'You do not have permission to declare war!'}
                
                # Check if target alliance exists
                target_alliance = self.sheets.get_alliance(target_alliance_id)
                if not target_alliance:
                    return {'success': False, 'message': 'Target alliance not found!'}
                
                # Check if already at war
                war_history = json.loads(alliance['war_history']) if alliance['war_history'] else []
                for war in war_history:
                    if (war['alliance1_id'] == alliance_id and war['alliance2_id'] == target_alliance_id) or \
                       (war['alliance1_id'] == target_alliance_id and war['alliance2_id'] == alliance_id):
                        return {'success': False, 'message': 'Already at war with this alliance!'}
                
                # Create war
                war_id = f"war_{len(war_history) + 1}"
                war_data = {
                    'id': war_id,
                    'alliance1_id': alliance_id,
                    'alliance2_id': target_alliance_id,
                    'start_time': time.time(),
                    'end_time': time.time() + ALLIANCE_SETTINGS['war_duration'],
                    'score': {alliance_id: 0, target_alliance_id: 0}
                }
                war_history.append(war_data)
                alliance['war_history'] = json.dumps(war_history)
                self.sheets.upsert_alliance(alliance)
                return {'success': True, 'war': war_data}
        return {'success': False, 'message': 'You do not have permission to declare war!'}

    def _check_level_up(self, alliance_id: str):
        """Check if alliance can level up"""
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return
        
        current_level = float(alliance['level'])
        current_xp = float(alliance['xp'])
        required_xp = current_level * ALLIANCE_SETTINGS['xp_per_level']
        
        if current_xp >= required_xp:
            alliance['level'] = current_level + 1
            alliance['xp'] = current_xp - required_xp 