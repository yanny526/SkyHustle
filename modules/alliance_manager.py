"""
Alliance Manager Module
Handles alliances, membership, wars, and donations (per-player)
"""

import time
from typing import Dict, List, Optional

class AllianceManager:
    def __init__(self):
        self.alliances: Dict[str, Dict] = {}  # alliance_id -> alliance info
        self.player_alliance: Dict[str, str] = {}  # player_id -> alliance_id
        self.join_requests: Dict[str, List[str]] = {}  # alliance_id -> list of player_ids
        self.alliance_resources: Dict[str, Dict[str, int]] = {}  # alliance_id -> resources
        self.alliance_perks: Dict[str, List[Dict]] = {}  # alliance_id -> perks
        self.alliance_benefits: Dict[str, List[Dict]] = {}  # alliance_id -> benefits
        self.alliance_research: Dict[str, List[Dict]] = {}  # alliance_id -> research
        self.alliance_diplomacy: Dict[str, List[Dict]] = {}  # alliance_id -> diplomacy
        self.alliance_wars: List[Dict] = []

    def create_alliance(self, player_id: str, name: str, description: str) -> Dict:
        if name in [a['name'] for a in self.alliances.values()]:
            return {'success': False, 'message': 'Alliance name already taken'}
        alliance_id = f"A{int(time.time()*1000)}"
        self.alliances[alliance_id] = {
            'alliance_id': alliance_id,
            'name': name,
            'description': description,
            'leader': player_id,
            'members': [player_id],
            'created_at': time.time(),
            'level': 1,
            'officers': [],
            'wars_won': 0,
            'points': 0,
            'rank': None
        }
        self.player_alliance[player_id] = alliance_id
        return {'success': True, 'alliance_id': alliance_id}

    def get_player_alliance(self, player_id: str) -> Optional[Dict]:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return None
        return {'success': True, 'alliance': self.alliances[alliance_id]}

    def get_all_alliances(self) -> List[Dict]:
        return list(self.alliances.values())

    def get_alliance(self, alliance_id: str) -> Optional[Dict]:
        return self.alliances.get(alliance_id)

    def join_alliance(self, player_id: str, alliance_id: str) -> Dict:
        if player_id in self.player_alliance:
            return {'success': False, 'message': 'Already in an alliance'}
        if alliance_id not in self.alliances:
            return {'success': False, 'message': 'Alliance not found'}
        self.alliances[alliance_id]['members'].append(player_id)
        self.player_alliance[player_id] = alliance_id
        return {'success': True}

    def get_join_requests(self, player_id: str) -> List[Dict]:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return []
        return [{'player_id': pid} for pid in self.join_requests.get(alliance_id, [])]

    def donate_resources(self, player_id: str, alliance_id: str, resources: Dict[str, int]) -> Dict:
        if alliance_id not in self.alliances:
            return {'success': False, 'message': 'Alliance not found'}
        if alliance_id not in self.alliance_resources:
            self.alliance_resources[alliance_id] = {}
        for resource, amount in resources.items():
            self.alliance_resources[alliance_id][resource] = self.alliance_resources[alliance_id].get(resource, 0) + amount
        return {'success': True}

    def get_alliance_resources(self, player_id: str) -> Dict:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return {}
        return self.alliance_resources.get(alliance_id, {})

    def get_alliance_perks(self, player_id: str) -> List[Dict]:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return []
        return self.alliance_perks.get(alliance_id, [])

    def get_alliance_benefits(self, player_id: str) -> List[Dict]:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return []
        return self.alliance_benefits.get(alliance_id, [])

    def get_alliance_research(self, player_id: str) -> List[Dict]:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return []
        return self.alliance_research.get(alliance_id, [])

    def get_alliance_diplomacy(self, player_id: str) -> List[Dict]:
        alliance_id = self.player_alliance.get(player_id)
        if not alliance_id:
            return []
        return self.alliance_diplomacy.get(alliance_id, [])

    def get_active_wars(self) -> List[Dict]:
        return self.alliance_wars

    def end_war(self, war_id: str):
        self.alliance_wars = [w for w in self.alliance_wars if w['id'] != war_id] 