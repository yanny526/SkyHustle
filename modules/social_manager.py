"""
Social Manager Module
Handles friends, chat, and social features (per-player)
"""

import time
from typing import Dict, List, Optional

class SocialManager:
    def __init__(self):
        self.friends: Dict[str, List[Dict]] = {}
        self.friend_requests = {}  # Store pending friend requests
        self.chat_messages = {}  # Store chat messages
        self.player_status = {}  # Store player online status
        self.last_activity = {}  # Track last activity time
        self.blocked_players = {}  # Store blocked players
        
        # Chat settings
        self.chat_settings = {
            'message_cooldown': 5,  # Seconds between messages
            'max_message_length': 200,
            'max_friends': 50,
            'max_blocked': 20
        }

    def send_friend_request(self, sender_id: str, receiver_id: str) -> Dict:
        """Send a friend request to another player"""
        # Check if already friends
        if self._are_friends(sender_id, receiver_id):
            return {'success': False, 'message': 'Already friends with this player'}
        
        # Check if request already exists
        if receiver_id in self.friend_requests and sender_id in self.friend_requests[receiver_id]:
            return {'success': False, 'message': 'Friend request already sent'}
        
        # Check if blocked
        if self._is_blocked(sender_id, receiver_id):
            return {'success': False, 'message': 'Cannot send friend request to blocked player'}
        
        # Add friend request
        if receiver_id not in self.friend_requests:
            self.friend_requests[receiver_id] = []
        self.friend_requests[receiver_id].append({
            'sender_id': sender_id,
            'timestamp': time.time()
        })
        
        return {'success': True, 'message': 'Friend request sent'}

    def accept_friend_request(self, player_id: str, sender_id: str) -> Dict:
        """Accept a friend request"""
        # Check if request exists
        if player_id not in self.friend_requests or not any(
            req['sender_id'] == sender_id for req in self.friend_requests[player_id]
        ):
            return {'success': False, 'message': 'No friend request found'}
        
        # Add friend relationship
        if player_id not in self.friends:
            self.friends[player_id] = []
        if sender_id not in self.friends:
            self.friends[sender_id] = []
        
        self.friends[player_id].append(sender_id)
        self.friends[sender_id].append(player_id)
        
        # Remove friend request
        self.friend_requests[player_id] = [
            req for req in self.friend_requests[player_id]
            if req['sender_id'] != sender_id
        ]
        
        return {'success': True, 'message': 'Friend request accepted'}

    def remove_friend(self, player_id: str, friend_id: str) -> Dict:
        """Remove a friend"""
        if not self._are_friends(player_id, friend_id):
            return {'success': False, 'message': 'Not friends with this player'}
        
        # Remove friend relationship
        self.friends[player_id].remove(friend_id)
        self.friends[friend_id].remove(player_id)
        
        return {'success': True, 'message': 'Friend removed'}

    def block_player(self, player_id: str, target_id: str) -> Dict:
        """Block another player"""
        # Check if already blocked
        if self._is_blocked(player_id, target_id):
            return {'success': False, 'message': 'Player already blocked'}
        
        # Check block limit
        if len(self.blocked_players.get(player_id, [])) >= self.chat_settings['max_blocked']:
            return {'success': False, 'message': 'Maximum number of blocked players reached'}
        
        # Add to blocked list
        if player_id not in self.blocked_players:
            self.blocked_players[player_id] = []
        self.blocked_players[player_id].append(target_id)
        
        # Remove friend relationship if exists
        if self._are_friends(player_id, target_id):
            self.remove_friend(player_id, target_id)
        
        return {'success': True, 'message': 'Player blocked'}

    def unblock_player(self, player_id: str, target_id: str) -> Dict:
        """Unblock a player"""
        if not self._is_blocked(player_id, target_id):
            return {'success': False, 'message': 'Player not blocked'}
        
        self.blocked_players[player_id].remove(target_id)
        return {'success': True, 'message': 'Player unblocked'}

    def send_chat_message(self, sender_id: str, receiver_id: str, message: str) -> Dict:
        """Send a chat message to another player"""
        # Check message length
        if len(message) > self.chat_settings['max_message_length']:
            return {'success': False, 'message': 'Message too long'}
        
        # Check cooldown
        if not self._can_send_message(sender_id):
            return {'success': False, 'message': 'Please wait before sending another message'}
        
        # Check if blocked
        if self._is_blocked(sender_id, receiver_id):
            return {'success': False, 'message': 'Cannot send message to blocked player'}
        
        # Store message
        if receiver_id not in self.chat_messages:
            self.chat_messages[receiver_id] = []
        
        self.chat_messages[receiver_id].append({
            'sender_id': sender_id,
            'message': message,
            'timestamp': time.time()
        })
        
        # Update last activity
        self.last_activity[sender_id] = time.time()
        
        return {'success': True, 'message': 'Message sent'}

    def get_chat_history(self, player_id: str, other_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history between two players"""
        if player_id not in self.chat_messages:
            return []
        
        # Get messages between these players
        messages = [
            msg for msg in self.chat_messages[player_id]
            if msg['sender_id'] == other_id
        ]
        
        # Sort by timestamp
        messages.sort(key=lambda x: x['timestamp'])
        
        return messages[-limit:]

    def get_friend_list(self, player_id: str) -> List[Dict]:
        """Get player's friend list with online status"""
        return self.friends.get(player_id, [])

    def get_friend_requests(self, player_id: str) -> List[Dict]:
        """Get pending friend requests"""
        if player_id not in self.friend_requests:
            return []
        
        return self.friend_requests[player_id]

    def update_player_status(self, player_id: str, status: str) -> None:
        """Update player's online status"""
        self.player_status[player_id] = {
            'status': status,
            'timestamp': time.time()
        }
        self.last_activity[player_id] = time.time()

    def _are_friends(self, player_id: str, other_id: str) -> bool:
        """Check if two players are friends"""
        return (
            player_id in self.friends and
            other_id in self.friends[player_id]
        )

    def _is_blocked(self, player_id: str, target_id: str) -> bool:
        """Check if a player is blocked"""
        return (
            player_id in self.blocked_players and
            target_id in self.blocked_players[player_id]
        )

    def _is_online(self, player_id: str) -> bool:
        """Check if a player is online"""
        if player_id not in self.player_status:
            return False
        
        last_seen = self.player_status[player_id]['timestamp']
        return time.time() - last_seen < 300  # 5 minutes

    def _can_send_message(self, player_id: str) -> bool:
        """Check if player can send a message (cooldown)"""
        if player_id not in self.last_activity:
            return True
        
        time_since_last = time.time() - self.last_activity[player_id]
        return time_since_last >= self.chat_settings['message_cooldown']

    def add_friend(self, player_id: str, friend_id: str) -> bool:
        if player_id not in self.friends:
            self.friends[player_id] = []
        if any(f['player_id'] == friend_id for f in self.friends[player_id]):
            return False
        self.friends[player_id].append({'player_id': friend_id, 'online': False, 'last_seen': time.time()})
        return True 