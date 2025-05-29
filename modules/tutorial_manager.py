"""
Tutorial Manager Module
Handles new player tutorials and guidance
"""

import time
from typing import Dict, List, Optional

class TutorialManager:
    def __init__(self):
        self.tutorials = {
            'welcome': {
                'name': 'Welcome to SkyHustle 2',
                'steps': [
                    {
                        'message': 'Welcome to SkyHustle 2! Let\'s get you started on your journey to becoming a great commander!',
                        'action': 'none'
                    },
                    {
                        'message': 'First, let\'s set your name. Use /name <your_name> to choose your display name.',
                        'action': 'wait_for_name'
                    },
                    {
                        'message': 'Great! Now let\'s check your base status. Use /status to see your current resources and buildings.',
                        'action': 'wait_for_status'
                    }
                ]
            },
            'resources': {
                'name': 'Resource Management',
                'steps': [
                    {
                        'message': 'Resources are the foundation of your empire. You have four main resources:',
                        'action': 'none'
                    },
                    {
                        'message': '🪵 Wood: Used for basic buildings and units\n🪨 Stone: Used for advanced buildings\n💰 Gold: Used for special units and research\n🍖 Food: Used to maintain your army',
                        'action': 'none'
                    },
                    {
                        'message': 'Let\'s build your first resource building. Use /build to see available buildings.',
                        'action': 'wait_for_build'
                    }
                ]
            },
            'buildings': {
                'name': 'Building System',
                'steps': [
                    {
                        'message': 'Buildings are essential for your base. Each building has a specific purpose:',
                        'action': 'none'
                    },
                    {
                        'message': '🏭 Lumberhouse: Produces wood\n⛏️ Mine: Produces stone and gold\n🏪 Warehouse: Stores food\n🏰 Barracks: Trains military units\n🔬 Research Center: Unlocks technologies\n🏰 Defense Tower: Protects your base',
                        'action': 'none'
                    },
                    {
                        'message': 'Try building a Lumberhouse to start producing wood!',
                        'action': 'wait_for_lumberhouse'
                    }
                ]
            },
            'military': {
                'name': 'Military Training',
                'steps': [
                    {
                        'message': 'A strong army is crucial for defending your base and attacking others.',
                        'action': 'none'
                    },
                    {
                        'message': 'You can train different types of units:\n👥 Infantry: Basic military unit\n🛡️ Tank: Heavy armored unit\n🏹 Archer: Long-range unit\n🐎 Cavalry: Fast-moving unit',
                        'action': 'none'
                    },
                    {
                        'message': 'Let\'s train some infantry. Use /train to start training units.',
                        'action': 'wait_for_train'
                    }
                ]
            },
            'combat': {
                'name': 'Combat System',
                'steps': [
                    {
                        'message': 'Now that you have units, you can attack other players or defend your base.',
                        'action': 'none'
                    },
                    {
                        'message': 'Use /attack to start an attack. Remember to train enough units first!',
                        'action': 'wait_for_attack'
                    },
                    {
                        'message': 'You can also check your battle history with /history',
                        'action': 'none'
                    }
                ]
            }
        }
        self.player_progress = {}  # Store tutorial progress for each player
        self.starter_bonuses = {
            'resources': {
                'wood': 500,
                'stone': 300,
                'gold': 100,
                'food': 200
            },
            'buildings': {
                'lumberhouse': 1,
                'mine': 1
            },
            'units': {
                'infantry': 5
            },
            'protection': {
                'duration': 86400  # 24 hours of new player protection
            }
        }

    def start_tutorial(self, player_id: str) -> Dict:
        """Start the tutorial for a new player"""
        if player_id in self.player_progress:
            return {'success': False, 'message': 'Tutorial already started'}
        
        self.player_progress[player_id] = {
            'current_tutorial': 'welcome',
            'current_step': 0,
            'started_at': time.time(),
            'completed_steps': set()
        }
        
        # Grant starter bonus
        self._grant_starter_bonus(player_id)
        
        return {
            'success': True,
            'tutorial': self.tutorials['welcome'],
            'current_step': 0
        }

    def get_current_step(self, player_id: str) -> Optional[Dict]:
        """Get the current tutorial step for a player"""
        if player_id not in self.player_progress:
            return None
        
        progress = self.player_progress[player_id]
        tutorial = self.tutorials[progress['current_tutorial']]
        return tutorial['steps'][progress['current_step']]

    def advance_tutorial(self, player_id: str, action: str) -> Dict:
        """Advance the tutorial based on player action"""
        if player_id not in self.player_progress:
            return {'success': False, 'message': 'No tutorial in progress'}
        
        progress = self.player_progress[player_id]
        current_tutorial = self.tutorials[progress['current_tutorial']]
        current_step = current_tutorial['steps'][progress['current_step']]
        
        # Check if action matches expected action
        if current_step['action'] != 'none' and current_step['action'] != action:
            return {'success': False, 'message': 'Invalid action for current step'}
        
        # Mark step as completed
        progress['completed_steps'].add(f"{progress['current_tutorial']}_{progress['current_step']}")
        
        # Move to next step or tutorial
        progress['current_step'] += 1
        if progress['current_step'] >= len(current_tutorial['steps']):
            # Move to next tutorial
            tutorials = list(self.tutorials.keys())
            current_index = tutorials.index(progress['current_tutorial'])
            if current_index + 1 < len(tutorials):
                progress['current_tutorial'] = tutorials[current_index + 1]
                progress['current_step'] = 0
            else:
                # Tutorial completed
                return {'success': True, 'completed': True}
        
        return {
            'success': True,
            'tutorial': self.tutorials[progress['current_tutorial']],
            'current_step': progress['current_step']
        }

    def _grant_starter_bonus(self, player_id: str):
        """Grant starter bonus to new player"""
        # This method is called by the game handler which has access to the resource manager
        # The actual resource granting is handled in the game handler's handle_start method
        pass

    def get_starter_bonus(self) -> Dict:
        """Get the starter bonus configuration"""
        return self.starter_bonuses

    def is_protected(self, player_id: str) -> bool:
        """Check if player is under new player protection"""
        if player_id not in self.player_progress:
            return False
        
        progress = self.player_progress[player_id]
        protection_time = self.starter_bonuses['protection']['duration']
        return time.time() - progress['started_at'] < protection_time

    def get_tutorial_progress(self, player_id: str) -> Dict:
        """Get tutorial progress for a player"""
        if player_id not in self.player_progress:
            return {'success': False, 'message': 'No tutorial in progress'}
        
        progress = self.player_progress[player_id]
        completed = len(progress['completed_steps'])
        total = sum(len(tutorial['steps']) for tutorial in self.tutorials.values())
        
        return {
            'success': True,
            'current_tutorial': progress['current_tutorial'],
            'current_step': progress['current_step'],
            'completed_steps': completed,
            'total_steps': total,
            'progress_percentage': (completed / total) * 100
        } 