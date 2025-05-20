"""
Alliance Research Manager for SkyHustle 2
Handles alliance research projects, contributions, and benefits
"""

from typing import Dict, List, Optional
import time
from config.alliance_config import ALLIANCE_SETTINGS
from config.game_config import RESEARCH

class AllianceResearchManager:
    def __init__(self):
        self.active_research: Dict[str, Dict] = {}  # alliance_id -> active research
        self.research_history: Dict[str, List[Dict]] = {}  # alliance_id -> completed research
        self.contributions: Dict[str, Dict[str, Dict]] = {}  # alliance_id -> player_id -> contributions
        self.research_benefits: Dict[str, Dict] = {}  # alliance_id -> active benefits
        self.last_contribution: Dict[str, Dict[str, float]] = {}  # alliance_id -> {player_id: timestamp}
        self.daily_contributions: Dict[str, Dict[str, int]] = {}  # alliance_id -> {player_id: amount}

    def initialize_alliance_research(self, alliance_id: str) -> bool:
        """Initialize research system for a new alliance"""
        if alliance_id in self.active_research:
            return False
            
        self.active_research[alliance_id] = None
        self.research_history[alliance_id] = []
        self.contributions[alliance_id] = {}
        self.research_benefits[alliance_id] = {}
        return True

    def start_research(self, alliance_id: str, research_id: str) -> bool:
        """Start a new research project"""
        if alliance_id not in self.active_research:
            return False
            
        if self.active_research[alliance_id] is not None:
            return False
            
        if research_id not in RESEARCH:
            return False
            
        # Check if research is already completed
        if research_id in [r['research_id'] for r in self.research_history[alliance_id]]:
            return False
            
        # Check research cooldown
        current_time = time.time()
        if alliance_id in self.research_history:
            last_research = self.research_history[alliance_id][-1]
            time_since_last = current_time - last_research['completion_time']
            if time_since_last < ALLIANCE_SETTINGS['research']['contribution_cooldown']:
                return False
            
        # Initialize research project
        self.active_research[alliance_id] = {
            'research_id': research_id,
            'start_time': current_time,
            'total_contributions': 0,
            'required_contributions': RESEARCH[research_id]['cost'],
            'status': 'in_progress'
        }
        
        # Initialize contributions tracking
        self.contributions[alliance_id] = {}
        self.daily_contributions[alliance_id] = {}
        
        return True

    def contribute_resources(self, alliance_id: str, player_id: str, resources: Dict[str, int]) -> bool:
        """Contribute resources to current research project"""
        if alliance_id not in self.active_research or self.active_research[alliance_id] is None:
            return False
            
        research = self.active_research[alliance_id]
        if research['status'] != 'in_progress':
            return False
            
        # Check contribution cooldown
        current_time = time.time()
        if (alliance_id in self.last_contribution and 
            player_id in self.last_contribution[alliance_id]):
            time_since_last = current_time - self.last_contribution[alliance_id][player_id]
            if time_since_last < ALLIANCE_SETTINGS['research']['contribution_cooldown']:
                return False
                
        # Check daily contribution limit
        if alliance_id not in self.daily_contributions:
            self.daily_contributions[alliance_id] = {}
        if player_id not in self.daily_contributions[alliance_id]:
            self.daily_contributions[alliance_id][player_id] = 0
            
        # Calculate contribution value
        contribution_value = sum(resources.values())
        
        # Check minimum contribution
        if contribution_value < ALLIANCE_SETTINGS['research']['min_contribution']:
            return False
            
        # Check daily contribution limit
        if (self.daily_contributions[alliance_id][player_id] + contribution_value > 
            ALLIANCE_SETTINGS['research']['max_contribution_per_day']):
            return False
            
        # Update contributions
        if player_id not in self.contributions[alliance_id]:
            self.contributions[alliance_id][player_id] = {
                'total_contributed': 0,
                'last_contribution': 0
            }
            
        self.contributions[alliance_id][player_id]['total_contributed'] += contribution_value
        self.contributions[alliance_id][player_id]['last_contribution'] = current_time
        
        # Update daily contributions
        self.daily_contributions[alliance_id][player_id] += contribution_value
        
        # Update last contribution time
        if alliance_id not in self.last_contribution:
            self.last_contribution[alliance_id] = {}
        self.last_contribution[alliance_id][player_id] = current_time
        
        # Update total contributions
        research['total_contributions'] += contribution_value
        
        # Check if research is complete
        if research['total_contributions'] >= research['required_contributions']:
            self._complete_research(alliance_id)
            
        return True

    def _complete_research(self, alliance_id: str) -> None:
        """Complete current research project and apply benefits"""
        research = self.active_research[alliance_id]
        research['status'] = 'completed'
        research['completion_time'] = time.time()
        
        # Add to research history
        self.research_history[alliance_id].append({
            'research_id': research['research_id'],
            'completion_time': research['completion_time'],
            'contributions': self.contributions[alliance_id].copy()
        })
        
        # Apply research benefits
        self._apply_research_benefits(alliance_id, research['research_id'])
        
        # Clear active research
        self.active_research[alliance_id] = None
        self.contributions[alliance_id] = {}

    def _apply_research_benefits(self, alliance_id: str, research_id: str) -> None:
        """Apply benefits from completed research"""
        research_info = RESEARCH[research_id]
        
        if 'benefits' in research_info:
            for benefit_type, value in research_info['benefits'].items():
                if benefit_type not in self.research_benefits[alliance_id]:
                    self.research_benefits[alliance_id][benefit_type] = 0
                self.research_benefits[alliance_id][benefit_type] += value

    def get_active_research(self, alliance_id: str) -> Optional[Dict]:
        """Get current research project status"""
        if alliance_id not in self.active_research:
            return None
            
        return self.active_research[alliance_id]

    def get_research_history(self, alliance_id: str, limit: int = 10) -> List[Dict]:
        """Get recent research history"""
        if alliance_id not in self.research_history:
            return []
            
        return sorted(
            self.research_history[alliance_id],
            key=lambda x: x['completion_time'],
            reverse=True
        )[:limit]

    def get_contributions(self, alliance_id: str, player_id: str) -> Dict:
        """Get player's contributions to current research"""
        if (alliance_id not in self.contributions or 
            player_id not in self.contributions[alliance_id]):
            return {'total_contributed': 0, 'last_contribution': 0}
            
        return self.contributions[alliance_id][player_id]

    def get_research_benefits(self, alliance_id: str) -> Dict:
        """Get current research benefits"""
        if alliance_id not in self.research_benefits:
            return {}
            
        return self.research_benefits[alliance_id]

    def get_available_research(self, alliance_id: str) -> List[Dict]:
        """Get list of available research projects"""
        if alliance_id not in self.research_history:
            return []
            
        completed_research = [r['research_id'] for r in self.research_history[alliance_id]]
        
        available = []
        for research_id, research in RESEARCH.items():
            if research_id not in completed_research:
                # Check prerequisites
                if 'prerequisites' in research:
                    if not all(prereq in completed_research for prereq in research['prerequisites']):
                        continue
                available.append({
                    'research_id': research_id,
                    'name': research['name'],
                    'description': research['description'],
                    'cost': research['cost'],
                    'benefits': research.get('benefits', {})
                })
                
        return available

    def cancel_research(self, alliance_id: str) -> bool:
        """Cancel current research project"""
        if (alliance_id not in self.active_research or 
            self.active_research[alliance_id] is None):
            return False
            
        # Clear active research
        self.active_research[alliance_id] = None
        self.contributions[alliance_id] = {}
        return True 