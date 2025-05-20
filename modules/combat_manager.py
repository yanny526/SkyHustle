"""
Combat Manager Module
Handles battle mechanics, formations, and tactics
"""

import time
import random
from typing import Dict, List, Optional
from config.game_config import UNITS

class CombatManager:
    def __init__(self):
        self.battle_history = {}  # Store battle history
        self.rankings = {}  # Store player rankings
        self.leagues = {
            'bronze': {'min_rating': 0, 'max_rating': 1000},
            'silver': {'min_rating': 1000, 'max_rating': 2000},
            'gold': {'min_rating': 2000, 'max_rating': 3000},
            'platinum': {'min_rating': 3000, 'max_rating': 4000},
            'diamond': {'min_rating': 4000, 'max_rating': float('inf')}
        }
        
        # Battle formations
        self.formations = {
            'standard': {
                'name': 'Standard Formation',
                'description': 'Balanced formation with equal focus on attack and defense',
                'bonuses': {
                    'attack': 1.0,
                    'defense': 1.0,
                    'speed': 1.0
                }
            },
            'aggressive': {
                'name': 'Aggressive Formation',
                'description': 'Focus on maximum damage output',
                'bonuses': {
                    'attack': 1.3,
                    'defense': 0.7,
                    'speed': 1.2
                }
            },
            'defensive': {
                'name': 'Defensive Formation',
                'description': 'Focus on maximum survivability',
                'bonuses': {
                    'attack': 0.7,
                    'defense': 1.3,
                    'speed': 0.8
                }
            },
            'flanking': {
                'name': 'Flanking Formation',
                'description': 'Focus on speed and surprise attacks',
                'bonuses': {
                    'attack': 1.1,
                    'defense': 0.9,
                    'speed': 1.4
                }
            }
        }
        
        # Battle tactics
        self.tactics = {
            'direct_assault': {
                'name': 'Direct Assault',
                'description': 'Charge directly at the enemy',
                'bonuses': {
                    'attack': 1.2,
                    'defense': 0.8
                }
            },
            'hit_and_run': {
                'name': 'Hit and Run',
                'description': 'Quick attacks followed by retreat',
                'bonuses': {
                    'attack': 1.1,
                    'speed': 1.3
                }
            },
            'siege': {
                'name': 'Siege',
                'description': 'Slow but powerful attacks',
                'bonuses': {
                    'attack': 1.4,
                    'speed': 0.6
                }
            },
            'guerrilla': {
                'name': 'Guerrilla',
                'description': 'Unpredictable attacks from all sides',
                'bonuses': {
                    'attack': 1.1,
                    'defense': 1.1,
                    'speed': 1.1
                }
            }
        }

    def initiate_battle(self, attacker_id: str, defender_id: str, attacker_units: Dict[str, int], 
                       formation: str = 'standard', tactic: str = 'direct_assault') -> Dict:
        """Initiate a new battle"""
        battle_id = f"battle_{int(time.time())}_{random.randint(1000, 9999)}"
        
        battle = {
            'id': battle_id,
            'attacker_id': attacker_id,
            'defender_id': defender_id,
            'attacker_units': attacker_units,
            'formation': formation,
            'tactic': tactic,
            'start_time': time.time(),
            'end_time': None,
            'result': None
        }
        
        # Store battle
        if attacker_id not in self.battle_history:
            self.battle_history[attacker_id] = []
        if defender_id not in self.battle_history:
            self.battle_history[defender_id] = []
        
        self.battle_history[attacker_id].append(battle)
        self.battle_history[defender_id].append(battle)
        
        return {'success': True, 'battle': battle}

    def calculate_battle_result(self, battle_id: str, defender_units: Dict[str, int]) -> Dict:
        """Calculate the result of a battle"""
        # Find battle
        battle = None
        for player_id, battles in self.battle_history.items():
            for b in battles:
                if b['id'] == battle_id:
                    battle = b
                    break
            if battle:
                break
        
        if not battle:
            return {'success': False, 'message': 'Battle not found'}
        
        # Get formation and tactic bonuses
        formation = self.formations[battle['formation']]
        tactic = self.tactics[battle['tactic']]
        
        # Calculate total stats for each side
        attacker_stats = self._calculate_army_stats(battle['attacker_units'], formation, tactic)
        defender_stats = self._calculate_army_stats(defender_units, 'standard', 'direct_assault')
        
        # Calculate casualties
        attacker_casualties = self._calculate_casualties(battle['attacker_units'], defender_stats)
        defender_casualties = self._calculate_casualties(defender_units, attacker_stats)
        
        # Determine winner
        attacker_power = attacker_stats['total_attack'] * (1 - attacker_casualties['percentage'])
        defender_power = defender_stats['total_attack'] * (1 - defender_casualties['percentage'])
        
        winner = 'attacker' if attacker_power > defender_power else 'defender'
        
        # Calculate rating changes
        rating_changes = self._calculate_rating_changes(
            battle['attacker_id'],
            battle['defender_id'],
            winner,
            attacker_power,
            defender_power
        )
        
        # Update battle result
        battle['end_time'] = time.time()
        battle['result'] = {
            'winner': winner,
            'attacker_casualties': attacker_casualties['units'],
            'defender_casualties': defender_casualties['units'],
            'rating_change': rating_changes
        }
        
        return {
            'success': True,
            'battle': battle,
            'winner': winner,
            'attacker_casualties': attacker_casualties['units'],
            'defender_casualties': defender_casualties['units'],
            'rating_change': rating_changes
        }

    def _calculate_army_stats(self, units: Dict[str, int], formation: Dict, tactic: Dict) -> Dict:
        """Calculate total stats for an army"""
        total_attack = 0
        total_defense = 0
        total_hp = 0
        total_speed = 0
        
        for unit_id, count in units.items():
            unit = UNITS[unit_id]
            stats = unit['stats']
            
            # Apply formation and tactic bonuses
            attack = stats['attack'] * formation['bonuses']['attack'] * tactic['bonuses'].get('attack', 1.0)
            defense = stats['defense'] * formation['bonuses']['defense'] * tactic['bonuses'].get('defense', 1.0)
            speed = stats['speed'] * formation['bonuses']['speed'] * tactic['bonuses'].get('speed', 1.0)
            
            total_attack += attack * count
            total_defense += defense * count
            total_hp += stats['hp'] * count
            total_speed += speed * count
        
        return {
            'total_attack': total_attack,
            'total_defense': total_defense,
            'total_hp': total_hp,
            'total_speed': total_speed
        }

    def _calculate_casualties(self, units: Dict[str, int], enemy_stats: Dict) -> Dict:
        """Calculate casualties for an army"""
        total_casualties = 0
        unit_casualties = {}
        
        for unit_id, count in units.items():
            unit = UNITS[unit_id]
            stats = unit['stats']
            
            # Calculate damage taken
            damage = enemy_stats['total_attack'] * (1 - stats['defense'] / (stats['defense'] + 100))
            casualties = int(count * (damage / (stats['hp'] * count)))
            
            unit_casualties[unit_id] = min(casualties, count)
            total_casualties += unit_casualties[unit_id]
        
        return {
            'units': unit_casualties,
            'percentage': total_casualties / sum(units.values()) if units else 0
        }

    def _calculate_rating_changes(self, attacker_id: str, defender_id: str, winner: str,
                                attacker_power: float, defender_power: float) -> Dict:
        """Calculate rating changes for both players"""
        # Get current ratings
        attacker_rating = self.rankings.get(attacker_id, 1000)
        defender_rating = self.rankings.get(defender_id, 1000)
        
        # Calculate expected outcome
        expected_attacker = 1 / (1 + 10 ** ((defender_rating - attacker_rating) / 400))
        expected_defender = 1 - expected_attacker
        
        # Calculate actual outcome
        actual_attacker = 1 if winner == 'attacker' else 0
        actual_defender = 1 - actual_attacker
        
        # Calculate rating changes
        k_factor = 32  # Rating change multiplier
        attacker_change = int(k_factor * (actual_attacker - expected_attacker))
        defender_change = int(k_factor * (actual_defender - expected_defender))
        
        # Update ratings
        self.rankings[attacker_id] = attacker_rating + attacker_change
        self.rankings[defender_id] = defender_rating + defender_change
        
        return {
            'attacker': attacker_change,
            'defender': defender_change
        }

    def get_player_rankings(self, player_id: str) -> Dict:
        """Get player's ranking information"""
        rating = self.rankings.get(player_id, 1000)
        league = self.get_player_league(player_id)
        
        # Calculate rank
        rank = 1
        for pid, r in self.rankings.items():
            if r > rating:
                rank += 1
        
        return {
            'success': True,
            'rating': rating,
            'league': league,
            'rank': rank
        }

    def get_player_league(self, player_id: str) -> str:
        """Get player's league based on rating"""
        rating = self.rankings.get(player_id, 1000)
        
        for league, range in self.leagues.items():
            if range['min_rating'] <= rating < range['max_rating']:
                return league
        
        return 'bronze'

    def get_league_standings(self, league: str) -> List[Dict]:
        """Get standings for a specific league"""
        if league not in self.leagues:
            return []
        
        range = self.leagues[league]
        standings = []
        
        for player_id, rating in self.rankings.items():
            if range['min_rating'] <= rating < range['max_rating']:
                standings.append({
                    'player_id': player_id,
                    'rating': rating
                })
        
        # Sort by rating
        standings.sort(key=lambda x: x['rating'], reverse=True)
        
        return standings

    def get_battle_history(self, player_id: str, limit: int = 10) -> List[Dict]:
        """Get player's battle history"""
        if player_id not in self.battle_history:
            return []
        
        # Sort battles by end time
        battles = sorted(
            self.battle_history[player_id],
            key=lambda x: x['end_time'] if x['end_time'] else float('inf'),
            reverse=True
        )
        
        return battles[:limit] 