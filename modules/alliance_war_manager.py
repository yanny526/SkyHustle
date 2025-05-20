"""
Alliance War Manager for SkyHustle 2
Handles alliance wars, battles, scoring, and rewards
"""

import time
import random
from typing import Dict, List, Optional, Tuple
from config.alliance_config import ALLIANCE_SETTINGS

class AllianceWarManager:
    def __init__(self):
        self.wars: Dict[str, Dict] = {}  # war_id -> war_data
        self.battles: Dict[str, List[Dict]] = {}  # war_id -> list of battles
        self.war_cooldowns: Dict[str, float] = {}  # alliance_id -> cooldown_end_time
        self.war_rewards: Dict[str, Dict] = {}  # war_id -> rewards
        self.battle_cooldowns: Dict[str, Dict[str, float]] = {}  # war_id -> {player_id: last_battle_time}

    def declare_war(self, alliance1_id: str, alliance2_id: str) -> Dict:
        """Declare war between two alliances"""
        # Check if either alliance is already at war
        for war in self.wars.values():
            if alliance1_id in [war['alliance1_id'], war['alliance2_id']] or \
               alliance2_id in [war['alliance1_id'], war['alliance2_id']]:
                return {'success': False, 'message': 'One or both alliances are already at war'}

        # Check war cooldown
        current_time = time.time()
        if alliance1_id in self.war_cooldowns and current_time < self.war_cooldowns[alliance1_id]:
            cooldown_left = int(self.war_cooldowns[alliance1_id] - current_time)
            return {'success': False, 'message': f'War cooldown active. {cooldown_left} seconds remaining'}

        # Create new war
        war_id = f"war_{int(current_time)}"
        self.wars[war_id] = {
            'id': war_id,
            'alliance1_id': alliance1_id,
            'alliance2_id': alliance2_id,
            'start_time': current_time,
            'end_time': current_time + ALLIANCE_SETTINGS['war_duration'],
            'score': {alliance1_id: 0, alliance2_id: 0},
            'status': 'preparation',  # preparation, active, ended
            'winner': None
        }
        self.battles[war_id] = []
        self.war_rewards[war_id] = {
            'winner': {},
            'loser': {}
        }

        return {'success': True, 'war_id': war_id}

    def start_war(self, war_id: str) -> Dict:
        """Start an active war after preparation period"""
        if war_id not in self.wars:
            return {'success': False, 'message': 'War not found'}

        war = self.wars[war_id]
        if war['status'] != 'preparation':
            return {'success': False, 'message': 'War is not in preparation phase'}

        current_time = time.time()
        if current_time < war['start_time'] + ALLIANCE_SETTINGS['war_preparation_time']:
            return {'success': False, 'message': 'Preparation period not over'}

        war['status'] = 'active'
        return {'success': True}

    def record_battle(self, war_id: str, attacker_id: str, defender_id: str, 
                     attacker_units: Dict, defender_units: Dict) -> Dict:
        """Record a battle between alliance members"""
        if war_id not in self.wars:
            return {'success': False, 'message': 'War not found'}

        war = self.wars[war_id]
        if war['status'] != 'active':
            return {'success': False, 'message': 'War is not active'}

        # Check battle cooldown for attacker
        current_time = time.time()
        if war_id in self.battle_cooldowns and attacker_id in self.battle_cooldowns[war_id]:
            time_since_last = current_time - self.battle_cooldowns[war_id][attacker_id]
            if time_since_last < ALLIANCE_SETTINGS['battle_cooldown']:
                return {'success': False, 'message': 'Battle cooldown active'}

        # Check daily battle limit
        if war_id in self.battles:
            today_battles = len([b for b in self.battles[war_id] 
                               if b['attacker_id'] == attacker_id and 
                               current_time - b['timestamp'] < 86400])
            if today_battles >= ALLIANCE_SETTINGS['max_battles_per_day']:
                return {'success': False, 'message': 'Daily battle limit reached'}

        # Calculate battle result
        attacker_power = sum(unit['power'] * count for unit, count in attacker_units.items())
        defender_power = sum(unit['power'] * count for unit, count in defender_units.items())

        # Add some randomness to battle outcome
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

        # Record battle
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

        self.battles[war_id].append(battle)

        # Update battle cooldown
        if war_id not in self.battle_cooldowns:
            self.battle_cooldowns[war_id] = {}
        self.battle_cooldowns[war_id][attacker_id] = current_time

        # Update war score
        if battle['winner'] == 'attacker':
            self.wars[war_id]['score'][war['alliance1_id']] += ALLIANCE_SETTINGS['scoring']['win_points']
        else:
            self.wars[war_id]['score'][war['alliance2_id']] += ALLIANCE_SETTINGS['scoring']['win_points']

        return {'success': True, 'battle': battle}

    def end_war(self, war_id: str) -> Dict:
        """End a war and calculate rewards"""
        if war_id not in self.wars:
            return {'success': False, 'message': 'War not found'}

        war = self.wars[war_id]
        if war['status'] == 'ended':
            return {'success': False, 'message': 'War already ended'}

        # Determine winner
        alliance1_score = war['score'][war['alliance1_id']]
        alliance2_score = war['score'][war['alliance2_id']]

        if alliance1_score > alliance2_score:
            winner_id = war['alliance1_id']
            loser_id = war['alliance2_id']
        elif alliance2_score > alliance1_score:
            winner_id = war['alliance2_id']
            loser_id = war['alliance1_id']
        else:
            winner_id = None
            loser_id = None

        # Calculate rewards
        total_battles = len(self.battles[war_id])
        if winner_id:
            # Winner gets 70% of total war points
            winner_points = int(total_battles * 0.7)
            loser_points = total_battles - winner_points

            self.war_rewards[war_id] = {
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
            # Draw - split points evenly
            points = total_battles // 2
            self.war_rewards[war_id] = {
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

        # Update war status
        war['status'] = 'ended'
        war['winner'] = winner_id

        # Set war cooldown for both alliances
        current_time = time.time()
        self.war_cooldowns[war['alliance1_id']] = current_time + ALLIANCE_SETTINGS['war_cooldown']
        self.war_cooldowns[war['alliance2_id']] = current_time + ALLIANCE_SETTINGS['war_cooldown']

        return {
            'success': True,
            'winner': winner_id,
            'rewards': self.war_rewards[war_id]
        }

    def get_war_status(self, war_id: str) -> Dict:
        """Get current status of a war"""
        if war_id not in self.wars:
            return {'success': False, 'message': 'War not found'}

        war = self.wars[war_id]
        return {
            'success': True,
            'war': war,
            'battles': self.battles[war_id],
            'rewards': self.war_rewards[war_id] if war['status'] == 'ended' else None
        }

    def get_alliance_wars(self, alliance_id: str) -> Dict:
        """Get all wars for an alliance"""
        alliance_wars = []
        for war in self.wars.values():
            if alliance_id in [war['alliance1_id'], war['alliance2_id']]:
                alliance_wars.append(war)

        return {
            'success': True,
            'wars': alliance_wars
        }

    def get_war_rankings(self) -> Dict:
        """Get alliance war rankings"""
        alliance_stats = {}
        for war in self.wars.values():
            if war['status'] == 'ended':
                for alliance_id in [war['alliance1_id'], war['alliance2_id']]:
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