"""
Alliance War Manager for SkyHustle 2
Handles alliance wars, battles, scoring, and rewards
"""

import time
import random
import json
from typing import Dict, List, Optional, Tuple
from config.alliance_config import ALLIANCE_SETTINGS
from modules.google_sheets_manager import GoogleSheetsManager

class AllianceWarManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

    def declare_war(self, alliance1_id: str, alliance2_id: str) -> Dict:
        """Declare war between two alliances"""
        # Check if either alliance is already at war
        for war in self.sheets.get_worksheet('AllianceWars').get_all_records():
            if alliance1_id in [war['attacker_id'], war['defender_id']] or \
               alliance2_id in [war['attacker_id'], war['defender_id']]:
                return {'success': False, 'message': 'One or both alliances are already at war'}
        # Check war cooldown (not implemented here, can be added as needed)
        current_time = time.time()
        war_id = f"war_{int(current_time)}"
        war_data = {
            'war_id': war_id,
            'attacker_id': alliance1_id,
            'defender_id': alliance2_id,
            'start_time': current_time,
            'end_time': current_time + ALLIANCE_SETTINGS['war_duration'],
            'status': 'preparation',
            'score': json.dumps({alliance1_id: 0, alliance2_id: 0}),
            'battles': json.dumps([]),
            'rewards': json.dumps({}),
            'winner': ''
        }
        self.sheets.log_alliance_war(war_data)
        return {'success': True, 'war_id': war_id}

    def get_war(self, war_id: str) -> Optional[Dict]:
        for war in self.sheets.get_worksheet('AllianceWars').get_all_records():
            if war['war_id'] == war_id:
                # Decode JSON fields
                war['score'] = json.loads(war['score']) if war['score'] else {}
                war['battles'] = json.loads(war['battles']) if war['battles'] else []
                war['rewards'] = json.loads(war['rewards']) if war['rewards'] else {}
                return war
        return None

    def start_war(self, war_id: str) -> Dict:
        """Start an active war after preparation period"""
        war = self.get_war(war_id)
        if not war:
            return {'success': False, 'message': 'War not found'}
        if war['status'] != 'preparation':
            return {'success': False, 'message': 'War is not in preparation phase'}
        current_time = time.time()
        if current_time < float(war['start_time']) + ALLIANCE_SETTINGS['war_preparation_time']:
            return {'success': False, 'message': 'Preparation period not over'}
        war['status'] = 'active'
        self._update_war(war)
        return {'success': True}

    def record_battle(self, war_id: str, attacker_id: str, defender_id: str, attacker_units: Dict, defender_units: Dict) -> Dict:
        """Record a battle between alliance members"""
        war = self.get_war(war_id)
        if not war:
            return {'success': False, 'message': 'War not found'}
        if war['status'] != 'active':
            return {'success': False, 'message': 'War is not active'}
        current_time = time.time()
        battles = war['battles']
        # Calculate battle result
        attacker_power = sum(unit['power'] * count for unit, count in attacker_units.items())
        defender_power = sum(unit['power'] * count for unit, count in defender_units.items())
        attacker_roll = random.uniform(
            ALLIANCE_SETTINGS['battle_settings']['random_factor']['min'],
            ALLIANCE_SETTINGS['battle_settings']['random_factor']['max']
        )
        defender_roll = random.uniform(
            ALLIANCE_SETTINGS['battle_settings']['random_factor']['min'],
            ALLIANCE_SETTINGS['battle_settings']['random_factor']['max']
        )
        attacker_final = attacker_power * attacker_roll
        defender_final = defender_power * defender_roll
        battle = {
            'timestamp': current_time,
            'attacker_id': attacker_id,
            'defender_id': defender_id,
            'attacker_units': attacker_units,
            'defender_units': defender_units,
            'attacker_power': attacker_final,
            'defender_power': defender_final,
            'winner': 'attacker' if attacker_final > defender_final else 'defender'
        }
        battles.append(battle)
        # Update war score
        score = war['score']
        if battle['winner'] == 'attacker':
            score[war['attacker_id']] += ALLIANCE_SETTINGS['scoring']['win_points']
        else:
            score[war['defender_id']] += ALLIANCE_SETTINGS['scoring']['win_points']
        war['battles'] = battles
        war['score'] = score
        self._update_war(war)
        return {'success': True, 'battle': battle}

    def end_war(self, war_id: str) -> Dict:
        """End a war and calculate rewards"""
        war = self.get_war(war_id)
        if not war:
            return {'success': False, 'message': 'War not found'}
        if war['status'] == 'ended':
            return {'success': False, 'message': 'War already ended'}
        # Determine winner
        alliance1_score = war['score'][war['attacker_id']]
        alliance2_score = war['score'][war['defender_id']]
        if alliance1_score > alliance2_score:
            winner_id = war['attacker_id']
            loser_id = war['defender_id']
        elif alliance2_score > alliance1_score:
            winner_id = war['defender_id']
            loser_id = war['attacker_id']
        else:
            winner_id = None
            loser_id = None
        # Calculate rewards (simplified)
        total_battles = len(war['battles'])
        if winner_id:
            winner_points = int(total_battles * 0.7)
            loser_points = total_battles - winner_points
            rewards = {
                'winner': {
                    'points': winner_points,
                    'resources': {
                        'gold': winner_points * 1000,
                        'wood': winner_points * 500,
                        'stone': winner_points * 300,
                        'food': winner_points * 800
                    }
                },
                'loser': {
                    'points': loser_points,
                    'resources': {
                        'gold': loser_points * 500,
                        'wood': loser_points * 250,
                        'stone': loser_points * 150,
                        'food': loser_points * 400
                    }
                }
            }
        else:
            points = total_battles // 2
            rewards = {
                'winner': {
                    'points': points,
                    'resources': {
                        'gold': points * 750,
                        'wood': points * 375,
                        'stone': points * 225,
                        'food': points * 600
                    }
                },
                'loser': {
                    'points': points,
                    'resources': {
                        'gold': points * 750,
                        'wood': points * 375,
                        'stone': points * 225,
                        'food': points * 600
                    }
                }
            }
        war['rewards'] = rewards
        war['status'] = 'ended'
        war['winner'] = winner_id
        self._update_war(war)
        return {'success': True, 'winner': winner_id, 'rewards': rewards}

    def get_war_status(self, war_id: str) -> Dict:
        """Get current status of a war"""
        war = self.get_war(war_id)
        if not war:
            return {'success': False, 'message': 'War not found'}
        return {
            'success': True,
            'war': war,
            'battles': war['battles'],
            'rewards': war['rewards'] if war['status'] == 'ended' else None
        }

    def get_alliance_wars(self, alliance_id: str) -> Dict:
        """Get all wars for an alliance"""
        alliance_wars = []
        for war in self.sheets.get_worksheet('AllianceWars').get_all_records():
            if alliance_id in [war['attacker_id'], war['defender_id']]:
                alliance_wars.append(war)

        return {
            'success': True,
            'wars': alliance_wars
        }

    def get_war_rankings(self) -> Dict:
        """Get alliance war rankings"""
        alliance_stats = {}
        for war in self.sheets.get_worksheet('AllianceWars').get_all_records():
            if war['status'] == 'ended':
                for alliance_id in [war['attacker_id'], war['defender_id']]:
                    if alliance_id not in alliance_stats:
                        alliance_stats[alliance_id] = {
                            'wars': 0,
                            'wins': 0,
                            'losses': 0,
                            'draws': 0,
                            'points': 0
                        }
                    
                    stats = alliance_stats[alliance_id]
                    stats['wars'] += 1
                    
                    if war['winner'] == alliance_id:
                        stats['wins'] += 1
                        stats['points'] += 3
                    elif war['winner'] is None:
                        stats['draws'] += 1
                        stats['points'] += 1
                    else:
                        stats['losses'] += 1

        # Sort alliances by points
        rankings = sorted(
            alliance_stats.items(),
            key=lambda x: (x[1]['points'], x[1]['wins']),
            reverse=True
        )

        return {
            'success': True,
            'rankings': [
                {
                    'alliance_id': alliance_id,
                    'stats': stats
                }
                for alliance_id, stats in rankings
            ]
        }

    def _update_war(self, war: Dict):
        # Update the war record in Google Sheets
        ws = self.sheets.get_worksheet('AllianceWars')
        all_wars = ws.get_all_records()
        for idx, row in enumerate(all_wars, start=2):
            if row['war_id'] == war['war_id']:
                # Prepare JSON fields
                war_row = {k: war[k] for k in war if k in row}
                war_row['score'] = json.dumps(war['score'])
                war_row['battles'] = json.dumps(war['battles'])
                war_row['rewards'] = json.dumps(war['rewards'])
                cell_list = ws.range(f'A{idx}:G{idx}')
                for i, key in enumerate(['war_id', 'attacker_id', 'defender_id', 'start_time', 'end_time', 'status', 'winner']):
                    cell_list[i].value = war_row.get(key, '')
                ws.update_cells(cell_list)
                # Update JSON fields
                ws.update(f'H{idx}', war_row['score'])
                ws.update(f'I{idx}', war_row['battles'])
                ws.update(f'J{idx}', war_row['rewards'])
                return 