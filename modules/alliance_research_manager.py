"""
Alliance Research Manager for SkyHustle 2
Handles alliance research projects, contributions, and benefits
"""

from typing import Dict, List, Optional
import time
import json
from config.alliance_config import ALLIANCE_SETTINGS
from config.game_config import RESEARCH
from modules.google_sheets_manager import GoogleSheetsManager

class AllianceResearchManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

    def initialize_alliance_research(self, alliance_id: str) -> bool:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        if 'active_research' in alliance:
            return False
        alliance['active_research'] = json.dumps(None)
        alliance['research_history'] = json.dumps([])
        alliance['contributions'] = json.dumps({})
        alliance['research_benefits'] = json.dumps({})
        self.sheets.upsert_alliance(alliance)
        return True

    def start_research(self, alliance_id: str, research_id: str) -> bool:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        active_research = json.loads(alliance['active_research']) if 'active_research' in alliance and alliance['active_research'] else None
        research_history = json.loads(alliance['research_history']) if 'research_history' in alliance and alliance['research_history'] else []
        if active_research is not None:
            return False
        if research_id not in RESEARCH:
            return False
        if research_id in [r['research_id'] for r in research_history]:
            return False
        current_time = time.time()
        if research_history:
            last_research = research_history[-1]
            time_since_last = current_time - last_research['completion_time']
            if time_since_last < ALLIANCE_SETTINGS['research']['contribution_cooldown']:
                return False
        active_research = {
            'research_id': research_id,
            'start_time': current_time,
            'total_contributions': 0,
            'required_contributions': RESEARCH[research_id]['cost'],
            'status': 'in_progress'
        }
        alliance['active_research'] = json.dumps(active_research)
        alliance['contributions'] = json.dumps({})
        alliance['daily_contributions'] = json.dumps({})
        self.sheets.upsert_alliance(alliance)
        return True

    def contribute_resources(self, alliance_id: str, player_id: str, resources: Dict[str, int]) -> bool:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance:
            return False
        active_research = json.loads(alliance['active_research']) if 'active_research' in alliance and alliance['active_research'] else None
        if not active_research or active_research['status'] != 'in_progress':
            return False
        contributions = json.loads(alliance['contributions']) if 'contributions' in alliance and alliance['contributions'] else {}
        daily_contributions = json.loads(alliance['daily_contributions']) if 'daily_contributions' in alliance and alliance['daily_contributions'] else {}
        current_time = time.time()
        # Check cooldown (not implemented here, can be added)
        if player_id not in daily_contributions:
            daily_contributions[player_id] = 0
        contribution_value = sum(resources.values())
        if contribution_value < ALLIANCE_SETTINGS['research']['min_contribution']:
            return False
        if daily_contributions[player_id] + contribution_value > ALLIANCE_SETTINGS['research']['max_contribution_per_day']:
            return False
        if player_id not in contributions:
            contributions[player_id] = {'total_contributed': 0, 'last_contribution': 0}
        contributions[player_id]['total_contributed'] += contribution_value
        contributions[player_id]['last_contribution'] = current_time
        daily_contributions[player_id] += contribution_value
        active_research['total_contributions'] += contribution_value
        if active_research['total_contributions'] >= active_research['required_contributions']:
            self._complete_research(alliance, active_research, contributions)
            return True
        alliance['active_research'] = json.dumps(active_research)
        alliance['contributions'] = json.dumps(contributions)
        alliance['daily_contributions'] = json.dumps(daily_contributions)
        self.sheets.upsert_alliance(alliance)
        return True

    def _complete_research(self, alliance, research, contributions):
        research['status'] = 'completed'
        research['completion_time'] = time.time()
        research_history = json.loads(alliance['research_history']) if 'research_history' in alliance and alliance['research_history'] else []
        research_history.append({
            'research_id': research['research_id'],
            'completion_time': research['completion_time'],
            'contributions': contributions.copy()
        })
        self._apply_research_benefits(alliance, research['research_id'])
        alliance['active_research'] = json.dumps(None)
        alliance['contributions'] = json.dumps({})
        alliance['research_history'] = json.dumps(research_history)
        self.sheets.upsert_alliance(alliance)

    def _apply_research_benefits(self, alliance, research_id: str) -> None:
        research_info = RESEARCH[research_id]
        research_benefits = json.loads(alliance['research_benefits']) if 'research_benefits' in alliance and alliance['research_benefits'] else {}
        if 'benefits' in research_info:
            for benefit_type, value in research_info['benefits'].items():
                if benefit_type not in research_benefits:
                    research_benefits[benefit_type] = 0
                research_benefits[benefit_type] += value
        alliance['research_benefits'] = json.dumps(research_benefits)

    def get_active_research(self, alliance_id: str) -> Optional[Dict]:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'active_research' not in alliance:
            return None
        return json.loads(alliance['active_research']) if alliance['active_research'] else None

    def get_research_history(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'research_history' not in alliance:
            return []
        history = json.loads(alliance['research_history']) if alliance['research_history'] else []
        return sorted(history, key=lambda x: x['completion_time'], reverse=True)[:limit]

    def get_contributions(self, alliance_id: str, player_id: str) -> Dict:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'contributions' not in alliance:
            return {'total_contributed': 0, 'last_contribution': 0}
        contributions = json.loads(alliance['contributions']) if alliance['contributions'] else {}
        return contributions.get(player_id, {'total_contributed': 0, 'last_contribution': 0})

    def get_research_benefits(self, alliance_id: str) -> Dict:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'research_benefits' not in alliance:
            return {}
        return json.loads(alliance['research_benefits']) if alliance['research_benefits'] else {}

    def get_available_research(self, alliance_id: str) -> List[Dict]:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'research_history' not in alliance:
            return []
        completed_research = [r['research_id'] for r in json.loads(alliance['research_history'])] if alliance['research_history'] else []
        available = []
        for research_id, research_info in RESEARCH.items():
            if research_id not in completed_research:
                available.append({'research_id': research_id, **research_info})
        return available

    def cancel_research(self, alliance_id: str) -> bool:
        alliance = self.sheets.get_alliance(alliance_id)
        if not alliance or 'active_research' not in alliance:
            return False
        alliance['active_research'] = json.dumps(None)
        alliance['contributions'] = json.dumps({})
        self.sheets.upsert_alliance(alliance)
        return True 