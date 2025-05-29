"""
Game Handler Module
Handles core game commands and interactions
"""

from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from modules.game_manager import GameManager
from modules.player_manager import PlayerManager
from modules.alliance_manager import AllianceManager
from modules.achievement_manager import AchievementManager
from modules.friend_manager import FriendManager
from modules.shop_manager import ShopManager
from modules.black_market_manager import BlackMarketManager
from modules.bag_manager import BagManager
from modules.premium_manager import PremiumManager
from modules.admin_manager import AdminManager
from modules.building_manager import BuildingManager
from modules.resource_manager import ResourceManager
from modules.unit_manager import UnitManager
from modules.research_manager import ResearchManager
from modules.combat_manager import CombatManager
from modules.quest_manager import QuestManager
from modules.market_manager import MarketManager
from modules.chat_manager import ChatManager
import logging
import html
import time

logger = logging.getLogger(__name__)

class GameHandler(BaseHandler):
    """Handler for game-related commands"""
    
    def __init__(self, game_manager: GameManager, building_manager: BuildingManager, resource_manager: ResourceManager, unit_manager: UnitManager, research_manager: ResearchManager, combat_manager: CombatManager, quest_manager: QuestManager, market_manager: MarketManager, chat_manager: ChatManager):
        super().__init__()
        self.game_manager = game_manager
        self.building_manager = building_manager
        self.resource_manager = resource_manager
        self.unit_manager = unit_manager
        self.research_manager = research_manager
        self.combat_manager = combat_manager
        self.quest_manager = quest_manager
        self.market_manager = market_manager
        self.chat_manager = chat_manager
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with polished, emoji-rich, Telegram-friendly UI."""
        try:
            player_id = str(update.effective_user.id)
            result = self.game_manager.start_game(player_id)

            if result['success']:
                message = (
                    "<b>🎉 Welcome to <u>SkyHustle 2</u>! 🎮</b>\n\n"
                    "<b>Your adventure begins now!</b>\n\n"
                    "<b>What you can do:</b>\n"
                    "<b>📊</b> <b>/status</b> — Check your status\n"
                    "<b>🏪</b> <b>/shop</b> — Visit the shop\n"
                    "<b>🎒</b> <b>/bag</b> — View your inventory\n"
                    "<b>👥</b> <b>/friends</b> — Manage friends\n"
                    "<b>🤝</b> <b>/alliances</b> — Join an alliance\n"
                    "<b>💎</b> <b>/premium</b> — Get premium currency\n\n"
                    "Type <b>/help</b> for <u>all commands</u>! 💡"
                )
            else:
                message = (
                    "<b>❌ Error</b>\n\n"
                    f"<b>Failed to Start Game:</b> {result.get('message', 'Could not start game.')}"
                )

            await self.send_message(update, message)

        except Exception as e:
            logger.error(f"Error in handle_start: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            player_id = str(update.effective_user.id)
            status = self.game_manager.get_status(player_id)
            
            if not status:
                await self.send_message(
                    update,
                    self.formatter.bold("Could not fetch status. Try /start to begin your adventure! 🎮")
                )
                return
            
            # Format status
            sections = [{
                'title': 'Player Status 🎮',
                'items': [
                    {
                        'type': 'stat',
                        'name': stat['name'],
                        'value': str(stat['value']),
                        'emoji': stat.get('emoji', '📊')
                    }
                    for stat in status['stats']
                ]
            }]
            
            # Add resources section if available
            if 'resources' in status:
                sections.append({
                    'title': 'Resources 💰',
                    'items': [
                        {
                            'type': 'resource',
                            'name': resource['name'],
                            'value': str(resource['value']),
                            'emoji': resource.get('emoji', '💎')
                        }
                        for resource in status['resources']
                    ]
                })
            
            # Add achievements section if available
            if 'achievements' in status:
                sections.append({
                    'title': 'Recent Achievements 🏆',
                    'items': [
                        {
                            'type': 'achievement',
                            'name': achievement['name'],
                            'description': achievement['description'],
                            'emoji': achievement.get('emoji', '🏆')
                        }
                        for achievement in status['achievements']
                    ]
                })
            
            # Create keyboard
            keyboard = [
                [{'text': '🔄 Refresh', 'callback_data': 'status_refresh'}],
                [{'text': '🏪 Shop', 'callback_data': 'shop'}, {'text': '🎒 Bag', 'callback_data': 'bag'}],
                [{'text': '👥 Friends', 'callback_data': 'friends'}, {'text': '🤝 Alliances', 'callback_data': 'alliances'}]
            ]
            
            # Send formatted message
            message = self.format_message("Status", sections)
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_status: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command: provide a beautiful, emoji-rich help menu with command descriptions and examples."""
        try:
            sections = [{
                'title': '🕹️ <b>Game Commands</b>',
                'items': [
                    {'type': 'command', 'name': '🎮 /start', 'description': 'Start the game and create your account', 'example': '/start'},
                    {'type': 'command', 'name': '📊 /status', 'description': 'View your current game status', 'example': '/status'},
                    {'type': 'command', 'name': '🏗️ /build', 'description': 'Build and upgrade buildings', 'example': '/build'},
                    {'type': 'command', 'name': '🪖 /train', 'description': 'Train military units', 'example': '/train'},
                    {'type': 'command', 'name': '🔬 /research', 'description': 'Research new technologies', 'example': '/research'},
                    {'type': 'command', 'name': '⚔️ /attack', 'description': 'Attack other players', 'example': '/attack'},
                    {'type': 'command', 'name': '🎯 /quest', 'description': 'View and complete quests', 'example': '/quest'},
                    {'type': 'command', 'name': '🏪 /market', 'description': 'Trade resources in the market', 'example': '/market'},
                    {'type': 'command', 'name': '🏪 /shop', 'description': 'Purchase items and upgrades', 'example': '/shop'},
                    {'type': 'command', 'name': '🎒 /bag', 'description': 'View your inventory', 'example': '/bag'},
                    {'type': 'command', 'name': '🕵️‍♂️ /blackmarket', 'description': 'Access the black market', 'example': '/blackmarket'},
                    {'type': 'command', 'name': '🏆 /achievements', 'description': 'View your achievements', 'example': '/achievements'},
                    {'type': 'command', 'name': '🎁 /daily', 'description': 'Claim daily rewards', 'example': '/daily'},
                    {'type': 'command', 'name': '🌟 /prestige', 'description': 'Prestige your account', 'example': '/prestige'},
                    {'type': 'command', 'name': '👤 /profile', 'description': 'View your profile', 'example': '/profile'},
                    {'type': 'command', 'name': '🏅 /leaderboard', 'description': 'View the global leaderboard', 'example': '/leaderboard'},
                    {'type': 'command', 'name': '✏️ /name', 'description': 'Change your display name', 'example': '/name New Name'},
                    {'type': 'command', 'name': '💬 /chat', 'description': 'Send a message to global chat', 'example': '/chat Hello, world!'},
                    {'type': 'command', 'name': '🚫 /block', 'description': 'Block a player', 'example': '/block @username'},
                    {'type': 'command', 'name': '✅ /unblock', 'description': 'Unblock a player', 'example': '/unblock @username'},
                    {'type': 'command', 'name': '🏆 /level', 'description': 'View your level and XP', 'example': '/level'},
                    {'type': 'command', 'name': '✨ /skills', 'description': 'View and upgrade your skills', 'example': '/skills'}
                ]
            }]
            keyboard = [[{'text': '🔙 Main Menu', 'callback_data': 'status'}]]
            message = self.format_message("<b>📖 Help Menu</b>", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_help: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_friends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /friends command"""
        try:
            player_id = str(update.effective_user.id)
            friends = self.game_manager.get_friends(player_id)
            
            if not friends:
                await self.send_message(
                    update,
                    self.formatter.bold("You have no friends yet. Add some with /add_friend! 👥")
                )
                return
            
            # Format friends list
            sections = [{
                'title': 'Friends List 👥',
                'items': [
                    {
                        'type': 'friend',
                        'name': friend['name'],
                        'status': friend['status'],
                        'emoji': friend.get('emoji', '👤')
                    }
                    for friend in friends
                ]
            }]
            
            # Create keyboard
            keyboard = [
                [{'text': '➕ Add Friend', 'callback_data': 'add_friend'}],
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            
            # Send formatted message
            message = self.format_message("Friends", sections)
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_friends: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_add_friend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_friend command"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /add_friend &lt;player_id&gt; 👥")
                )
                return
            
            target_id = args[0]
            result = self.game_manager.add_friend(str(update.effective_user.id), target_id)
            
            if result['success']:
                message = self.format_message(
                    "Friend Added",
                    [{
                        'title': 'Success!',
                        'content': f"Added {target_id} as a friend! 👥"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Add Friend',
                        'content': result.get('message', 'Could not add friend.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_add_friend: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_remove_friend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remove_friend command"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /remove_friend &lt;player_id&gt; 👥")
                )
                return
            
            target_id = args[0]
            result = self.game_manager.remove_friend(str(update.effective_user.id), target_id)
            
            if result['success']:
                message = self.format_message(
                    "Friend Removed",
                    [{
                        'title': 'Success!',
                        'content': f"Removed {target_id} from friends. 👥"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Remove Friend',
                        'content': result.get('message', 'Could not remove friend.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_remove_friend: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_achievements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /achievements command: show player achievements and allow claiming rewards if completed."""
        try:
            player_id = str(update.effective_user.id)
            achievement_manager = self.game_manager.achievement_manager
            achievements = achievement_manager.get_achievements(player_id)
            if not achievements:
                await self.send_message(
                    update,
                    self.formatter.bold("No achievements found! 🏆")
                )
                return
            sections = [{
                'title': 'Achievements 🏆',
                'items': []
            }]
            keyboard = []
            for achievement in achievements:
                progress = achievement.get('progress', '0%')
                completed = achievement.get('completed', False)
                claimed = achievement.get('claimed', False)
                desc = f"{achievement.get('emoji', '🏆')} <b>{achievement['name']}</b>\n{achievement['description']}\nProgress: {progress}"
                sections[0]['items'].append({
                    'type': 'achievement',
                    'name': achievement['name'],
                    'description': desc,
                    'emoji': achievement.get('emoji', '🏆'),
                })
                if completed and not claimed:
                    keyboard.append([
                        {'text': f"Claim {achievement['name']} Reward", 'callback_data': f"achievement_claim_{achievement['id']}"}
                    ])
                elif claimed:
                    keyboard.append([
                        {'text': f"✅ {achievement['name']} Claimed", 'callback_data': 'noop'}
                    ])
                else:
                    keyboard.append([
                        {'text': f"In Progress: {achievement['name']}", 'callback_data': 'noop'}
                    ])
            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Achievements Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_achievements: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command: show player profile with stats, achievements, and other relevant information."""
        try:
            player_id = str(update.effective_user.id)
            player_manager = self.game_manager.player_manager
            profile = player_manager.get_player(player_id)
            if not profile:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            sections = [{
                'title': 'Player Profile 👤',
                'items': []
            }]
            for stat in profile.get('stats', []):
                sections[0]['items'].append({
                    'type': 'stat',
                    'name': stat['name'],
                    'value': str(stat['value']),
                    'emoji': stat.get('emoji', '📊')
                })
            if 'achievements' in profile:
                sections.append({
                    'title': 'Achievements 🏆',
                    'items': [
                        {
                            'type': 'achievement',
                            'name': achievement['name'],
                            'description': achievement['description'],
                            'emoji': achievement.get('emoji', '🏆')
                        }
                        for achievement in profile['achievements']
                    ]
                })
            keyboard = [[{'text': '🔙 Back', 'callback_data': 'status'}]]
            message = self.format_message("Profile", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_profile: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command: show daily reward status and allow claiming rewards if eligible."""
        try:
            player_id = str(update.effective_user.id)
            result = self.game_manager.claim_daily_reward(player_id)
            if result['success']:
                message = self.format_message(
                    "Daily Reward",
                    [{
                        'title': 'Success!',
                        'content': f"Claimed daily reward! 🎁\n\n{result.get('message', '')}"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Claim Daily Reward',
                        'content': result.get('message', 'Could not claim daily reward.')
                    }]
                )
            await self.send_message(update, message)
        except Exception as e:
            logger.error(f"Error in handle_daily: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_quest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quest command: show available quests, progress, and allow claiming rewards."""
        try:
            player_id = str(update.effective_user.id)
            quest_manager = self.quest_manager
            resource_manager = self.resource_manager

            # Get all available quests
            quests = quest_manager.get_quests(player_id)
            player_resources = resource_manager.get_resources(player_id)

            if not quests:
                await self.send_message(
                    update,
                    self.formatter.bold("No quests available! 🎯")
                )
                return

            sections = [{
                'title': 'Quests 🎯',
                'items': []
            }]
            keyboard = []

            for q in quests:
                progress = q.get('progress', '0%')
                completed = q.get('completed', False)
                reward_str = ', '.join(f"{k}: {v}" for k, v in q.get('reward', {}).items())
                desc = f"{q.get('emoji', '🎯')} <b>{q['name']}</b>\n{q['description']}\nProgress: {progress}\nReward: {reward_str}"
                sections[0]['items'].append({
                    'type': 'quest',
                    'name': q['name'],
                    'description': desc,
                    'emoji': q.get('emoji', '🎯'),
                })
                if completed and not q.get('claimed', False):
                    keyboard.append([
                        {'text': f"Claim {q['name']} Reward", 'callback_data': f"quest_claim_{q['id']}"}
                    ])
                elif completed and q.get('claimed', False):
                    keyboard.append([
                        {'text': f"✅ {q['name']} Claimed", 'callback_data': 'noop'}
                    ])
                else:
                    keyboard.append([
                        {'text': f"In Progress: {q['name']}", 'callback_data': 'noop'}
                    ])

            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Quest Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_quest: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leaderboard command: show global leaderboard with player rankings, scores, and other relevant information."""
        try:
            leaderboard = self.game_manager.player_manager.get_leaderboard()
            if not leaderboard:
                await self.send_message(
                    update,
                    self.formatter.bold("No leaderboard data available. 🏆")
                )
                return
            sections = [{
                'title': 'Global Leaderboard 🏆',
                'items': []
            }]
            for player in leaderboard:
                sections[0]['items'].append({
                    'type': 'player',
                    'name': player['name'],
                    'score': str(player['score']),
                    'rank': str(player['rank']),
                    'emoji': player.get('emoji', '👤')
                })
            keyboard = [[{'text': '🔙 Back', 'callback_data': 'status'}]]
            message = self.format_message("Leaderboard", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_leaderboard: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_tutorial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tutorial command"""
        try:
            player_id = str(update.effective_user.id)
            result = self.game_manager.start_tutorial(player_id)
            
            if result['success']:
                message = self.format_message(
                    "Tutorial",
                    [{
                        'title': 'Welcome to the Tutorial! 📚',
                        'content': result.get('message', 'Let\'s get started!')
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Start Tutorial',
                        'content': result.get('message', 'Could not start tutorial.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_tutorial: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rules command"""
        try:
            rules = self.game_manager.get_rules()
            
            if not rules:
                await self.send_message(
                    update,
                    self.formatter.bold("No rules available. 📜")
                )
                return
            
            # Format rules
            sections = [{
                'title': 'Game Rules 📜',
                'items': [
                    {
                        'type': 'rule',
                        'name': rule['name'],
                        'description': rule['description'],
                        'emoji': rule.get('emoji', '📜')
                    }
                    for rule in rules
                ]
            }]
            
            # Create keyboard
            keyboard = [
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            
            # Send formatted message
            message = self.format_message("Rules", sections)
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_rules: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_build(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /build command: show available buildings, their status, and upgrade options."""
        try:
            player_id = str(update.effective_user.id)
            # Assume self.building_manager and self.resource_manager are available
            building_manager = self.building_manager
            resource_manager = self.resource_manager

            # Update any completed upgrades
            building_manager.update_upgrades(player_id)

            # Get all available buildings
            available = building_manager.get_available_buildings(player_id)
            queue = building_manager.get_upgrade_queue(player_id)
            player_resources = resource_manager.get_resources(player_id)

            if not available:
                await self.send_message(
                    update,
                    self.formatter.bold("No buildings available to build or upgrade! 🏗️")
                )
                return

            sections = [{
                'title': 'Your Buildings 🏗️',
                'items': []
            }]
            keyboard = []

            for b in available:
                cost_str = ', '.join(f"{k}: {v}" for k, v in b['cost'].items())
                can_afford = resource_manager.can_afford(player_id, b['cost'])
                status = f"Level {b['level']}/{b['max_level']}"
                desc = f"{b['emoji']} <b>{b['name']}</b>\n{b['description']}\n{status}\nCost: {cost_str}"
                sections[0]['items'].append({
                    'type': 'building',
                    'name': b['name'],
                    'description': desc,
                    'emoji': b['emoji'],
                })
                if can_afford:
                    keyboard.append([
                        {'text': f"Upgrade {b['name']} ({status})", 'callback_data': f"build_upgrade_{b['id']}"}
                    ])
                else:
                    keyboard.append([
                        {'text': f"❌ Not enough resources for {b['name']}", 'callback_data': 'noop'}
                    ])

            # Show upgrade queue if any
            if queue:
                queue_str = "\n".join([
                    f"{building_manager.get_building_info(player_id, u['building_id'])['name']} upgrading to Lv{u['to_level']} (done in {int(u['end_time']-time.time())//60}m)"
                    for u in queue
                ])
                sections.append({
                    'title': 'Upgrade Queue ⏳',
                    'content': queue_str
                })

            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Build Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_build: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_train(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /train command: show available units, their status, and training options."""
        try:
            player_id = str(update.effective_user.id)
            unit_manager = self.unit_manager
            resource_manager = self.resource_manager

            # Update any completed training
            unit_manager.update_training(player_id)

            # Get all available units
            available = unit_manager.get_available_units(player_id)
            queue = unit_manager.get_training_queue(player_id)
            player_resources = resource_manager.get_resources(player_id)

            if not available:
                await self.send_message(
                    update,
                    self.formatter.bold("No units available to train! 🪖")
                )
                return

            sections = [{
                'title': 'Train Units 🪖',
                'items': []
            }]
            keyboard = []

            for u in available:
                cost_str = ', '.join(f"{k}: {v}" for k, v in u['cost'].items())
                can_afford = resource_manager.can_afford(player_id, u['cost'])
                status = f"Owned: {u['count']}"
                desc = f"{u['emoji']} <b>{u['name']}</b>\n{u['description']}\n{status}\nCost: {cost_str}"
                sections[0]['items'].append({
                    'type': 'unit',
                    'name': u['name'],
                    'description': desc,
                    'emoji': u['emoji'],
                })
                if can_afford:
                    keyboard.append([
                        {'text': f"Train {u['name']}", 'callback_data': f"train_unit_{u['id']}"}
                    ])
                else:
                    keyboard.append([
                        {'text': f"❌ Not enough resources for {u['name']}", 'callback_data': 'noop'}
                    ])

            # Show training queue if any
            if queue:
                queue_str = "\n".join([
                    f"{unit_manager.get_unit_info(player_id, unit_id)['name']} x{count} (training)"
                    for unit_id, count in queue.items()
                ])
                sections.append({
                    'title': 'Training Queue ⏳',
                    'content': queue_str
                })

            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Train Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_train: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /research command: show available research, their status, and research options."""
        try:
            player_id = str(update.effective_user.id)
            research_manager = self.research_manager
            resource_manager = self.resource_manager

            # Update any completed research (if your backend supports it)
            # research_manager.update_research(player_id)  # Uncomment if you have this method

            # Get all available research
            available = research_manager.get_all_research(player_id)
            queue = research_manager.get_research_queue(player_id)
            player_resources = resource_manager.get_resources(player_id)

            # Flatten available research into a list
            research_list = []
            for category, items in available.items():
                for research_id, research in items.items():
                    info = research['info']
                    level = research['level']
                    max_level = info.get('max_level', 10)
                    cost = research_manager.get_research_cost(player_id, research_id)
                    can_afford = resource_manager.can_afford(player_id, cost)
                    research_list.append({
                        'id': research_id,
                        'name': info['name'],
                        'emoji': info.get('emoji', '🔬'),
                        'description': info['description'],
                        'level': level,
                        'max_level': max_level,
                        'cost': cost,
                        'can_afford': can_afford
                    })

            if not research_list:
                await self.send_message(
                    update,
                    self.formatter.bold("No research available! 🔬")
                )
                return

            sections = [{
                'title': 'Research 🔬',
                'items': []
            }]
            keyboard = []

            for r in research_list:
                cost_str = ', '.join(f"{k}: {v}" for k, v in r['cost'].items())
                status = f"Level {r['level']}/{r['max_level']}"
                desc = f"{r['emoji']} <b>{r['name']}</b>\n{r['description']}\n{status}\nCost: {cost_str}"
                sections[0]['items'].append({
                    'type': 'research',
                    'name': r['name'],
                    'description': desc,
                    'emoji': r['emoji'],
                })
                if r['can_afford'] and r['level'] < r['max_level']:
                    keyboard.append([
                        {'text': f"Research {r['name']} ({status})", 'callback_data': f"research_start_{r['id']}"}
                    ])
                elif r['level'] >= r['max_level']:
                    keyboard.append([
                        {'text': f"✅ Max Level for {r['name']}", 'callback_data': 'noop'}
                    ])
                else:
                    keyboard.append([
                        {'text': f"❌ Not enough resources for {r['name']}", 'callback_data': 'noop'}
                    ])

            # Show research queue if any
            if queue:
                queue_str = "\n".join([
                    f"{research_manager.get_research_info(player_id, research_id)['name']} (done in {int(time_left)//60}m)"
                    for research_id, time_left in queue.items()
                ])
                sections.append({
                    'title': 'Research Queue ⏳',
                    'content': queue_str
                })

            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Research Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_research: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_attack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /attack command: show potential targets and allow player to attack."""
        try:
            player_id = str(update.effective_user.id)
            combat_manager = self.combat_manager
            unit_manager = self.unit_manager
            resource_manager = self.resource_manager
            player_manager = self.game_manager.player_manager

            # For now, show a list of all other players as potential targets (except self)
            all_players = player_manager.get_all_players()
            targets = [p for p in all_players if p['player_id'] != player_id]

            if not targets:
                await self.send_message(
                    update,
                    self.formatter.bold("No targets available to attack! 🗡️")
                )
                return

            sections = [{
                'title': 'Attack Targets 🗡️',
                'items': []
            }]
            keyboard = []

            for t in targets:
                name = t.get('name', f"Player {t['player_id'][:6]}")
                level = t.get('level', 1)
                power = t.get('power', '?')
                desc = f"👤 <b>{name}</b>\nLevel: {level}\nPower: {power}"
                sections[0]['items'].append({
                    'type': 'target',
                    'name': name,
                    'description': desc,
                    'emoji': '⚔️',
                })
                keyboard.append([
                    {'text': f"Attack {name}", 'callback_data': f"attack_select_{t['player_id']}"}
                ])

            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Attack Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_attack: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_market(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /market command: show available market items/resources and allow purchase/trade."""
        try:
            player_id = str(update.effective_user.id)
            market_manager = self.market_manager
            resource_manager = self.resource_manager

            # Get all available market items
            items = market_manager.get_market_items(player_id)
            player_resources = resource_manager.get_resources(player_id)

            if not items:
                await self.send_message(
                    update,
                    self.formatter.bold("No items available in the market! 🏪")
                )
                return

            sections = [{
                'title': 'Market 🏪',
                'items': []
            }]
            keyboard = []

            for item in items:
                cost_str = ', '.join(f"{k}: {v}" for k, v in item['cost'].items())
                can_afford = resource_manager.can_afford(player_id, item['cost'])
                desc = f"{item.get('emoji', '🏪')} <b>{item['name']}</b>\n{item['description']}\nCost: {cost_str}"
                sections[0]['items'].append({
                    'type': 'market_item',
                    'name': item['name'],
                    'description': desc,
                    'emoji': item.get('emoji', '🏪'),
                })
                if can_afford:
                    keyboard.append([
                        {'text': f"Buy {item['name']}", 'callback_data': f"market_buy_{item['id']}"}
                    ])
                else:
                    keyboard.append([
                        {'text': f"❌ Not enough resources for {item['name']}", 'callback_data': 'noop'}
                    ])

            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Market Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_market: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries, including shop, bag, black market, and achievements logic."""
        try:
            query = update.callback_query
            data = query.data
            player_id = str(query.from_user.id)
            if data.startswith('shop_buy_'):
                item_id = data.split('_', 2)[2]
                shop_manager = self.game_manager.shop_manager
                resource_manager = self.game_manager.resource_manager
                item = shop_manager.get_shop_item(item_id)
                if not item:
                    await query.answer("Item not found!", show_alert=True)
                    return
                if not resource_manager.can_afford(player_id, item['cost']):
                    await query.answer("Not enough resources!", show_alert=True)
                    return
                resource_manager.spend_resources(player_id, item['cost'])
                success, msg = shop_manager.buy_item(player_id, item_id)
                if success:
                    await query.answer("Purchase successful!", show_alert=True)
                else:
                    await query.answer(msg, show_alert=True)
                await self.handle_shop(update, context)
                return
            elif data.startswith('bag_use_'):
                item_id = data.split('_', 2)[2]
                bag_manager = self.game_manager.bag_manager
                success, msg = bag_manager.use_item(player_id, item_id)
                if success:
                    await query.answer("Item used successfully!", show_alert=True)
                else:
                    await query.answer(msg, show_alert=True)
                await self.handle_bag(update, context)
                return
            elif data.startswith('blackmarket_buy_'):
                item_id = data.split('_', 2)[2]
                black_market_manager = self.game_manager.black_market_manager
                resource_manager = self.game_manager.resource_manager
                item = black_market_manager.get_black_market_item(item_id)
                if not item:
                    await query.answer("Item not found!", show_alert=True)
                    return
                if not resource_manager.can_afford(player_id, item['cost']):
                    await query.answer("Not enough resources!", show_alert=True)
                    return
                resource_manager.spend_resources(player_id, item['cost'])
                success, msg = black_market_manager.buy_item(player_id, item_id)
                if success:
                    await query.answer("Purchase successful!", show_alert=True)
                else:
                    await query.answer(msg, show_alert=True)
                await self.handle_blackmarket(update, context)
                return
            elif data.startswith('achievement_claim_'):
                achievement_id = data.split('_', 2)[2]
                achievement_manager = self.game_manager.achievement_manager
                success, msg = achievement_manager.claim_achievement_reward(player_id, achievement_id)
                if success:
                    await query.answer("Reward claimed successfully!", show_alert=True)
                else:
                    await query.answer(msg, show_alert=True)
                await self.handle_achievements(update, context)
                return
            elif data.startswith('build_upgrade_'):
                building_id = data.split('_', 2)[2]
                building_manager = self.building_manager
                resource_manager = self.resource_manager
                binfo = building_manager.get_building_info(player_id, building_id)
                cost = building_manager.get_upgrade_cost(player_id, building_id)
                if not resource_manager.can_afford(player_id, cost):
                    await query.answer("Not enough resources!", show_alert=True)
                    return
                resource_manager.spend_resources(player_id, cost)
                success, msg = building_manager.queue_upgrade(player_id, building_id)
                if success:
                    await query.answer("Upgrade started!", show_alert=True)
                else:
                    await query.answer(msg, show_alert=True)
                await self.handle_build(update, context)
                return
            elif data.startswith('train_unit_'):
                unit_id = data.split('_', 2)[2]
                unit_manager = self.unit_manager
                resource_manager = self.resource_manager
                unit_info = unit_manager.get_unit_info(player_id, unit_id)
                cost = unit_manager.get_training_cost(unit_id)
                if not resource_manager.can_afford(player_id, cost):
                    await query.answer("Not enough resources!", show_alert=True)
                    return
                resource_manager.spend_resources(player_id, cost)
                unit_manager.queue_training(player_id, unit_id, count=1)
                await query.answer("Training started!", show_alert=True)
                await self.handle_train(update, context)
                return
            elif data.startswith('research_start_'):
                research_id = data.split('_', 2)[2]
                research_manager = self.research_manager
                resource_manager = self.resource_manager
                cost = research_manager.get_research_cost(player_id, research_id)
                if not resource_manager.can_afford(player_id, cost):
                    await query.answer("Not enough resources!", show_alert=True)
                    return
                resource_manager.spend_resources(player_id, cost)
                success = research_manager.queue_research(player_id, research_id)
                if success:
                    await query.answer("Research started!", show_alert=True)
                else:
                    await query.answer("Cannot start research!", show_alert=True)
                await self.handle_research(update, context)
                return
            elif data.startswith('attack_select_'):
                target_id = data.split('_', 2)[2]
                unit_manager = self.unit_manager
                available_units = unit_manager.get_army(player_id)
                if not available_units:
                    await query.answer("No units to send!", show_alert=True)
                    return
                context.user_data['attack_target'] = target_id
                context.user_data['attack_units'] = available_units
                keyboard = [
                    [{'text': 'Attack!', 'callback_data': f'attack_confirm_{target_id}'}],
                    [{'text': 'Cancel', 'callback_data': 'attack_cancel'}]
                ]
                unit_str = '\n'.join([f"{unit_manager.get_unit_info(player_id, uid).get('emoji', '🪖')} {unit_manager.get_unit_info(player_id, uid).get('name', uid)} x{count}" for uid, count in available_units.items()])
                message = f"<b>Confirm Attack</b>\nTarget: {target_id}\nYour Army:\n{unit_str}"
                await query.edit_message_text(message, reply_markup=self.create_keyboard(keyboard), parse_mode='HTML')
                return
            elif data.startswith('attack_confirm_'):
                target_id = data.split('_', 2)[2]
                combat_manager = self.combat_manager
                unit_manager = self.unit_manager
                army = context.user_data.get('attack_units', {})
                if not army:
                    await query.answer("No units selected!", show_alert=True)
                    return
                for uid, count in army.items():
                    unit_manager.units[player_id][uid]['count'] -= count
                defender_units = unit_manager.get_army(target_id)
                result = combat_manager.initiate_battle(player_id, target_id, army)
                winner = result.get('winner', 'unknown')
                report = f"<b>Battle Report</b>\nWinner: {winner}\n"
                report += f"Your Army: {army}\nDefender Army: {defender_units}\n"
                report += f"Details: {result.get('battle', {})}"
                await query.edit_message_text(report, parse_mode='HTML')
                context.user_data.pop('attack_target', None)
                context.user_data.pop('attack_units', None)
                return
            elif data == 'attack_cancel':
                await self.handle_attack(update, context)
                return
            elif data.startswith('quest_claim_'):
                quest_id = data.split('_', 2)[2]
                quest_manager = self.quest_manager
                success, msg = quest_manager.claim_quest_reward(player_id, quest_id)
                if success:
                    await query.answer("Reward claimed!", show_alert=True)
                else:
                    await query.answer(msg, show_alert=True)
                await self.handle_quest(update, context)
                return
            elif data.startswith('market_buy_'):
                item_id = data.split('_', 2)[2]
                market_manager = self.market_manager
                resource_manager = self.resource_manager
                result = market_manager.buy_item(player_id, item_id)
                if result.get('success'):
                    await query.answer("Purchase successful!", show_alert=True)
                else:
                    await query.answer(result.get('message', 'Could not buy item.'), show_alert=True)
                await self.handle_market(update, context)
                return
            await super().handle_callback(update, context)
        except Exception as e:
            logger.error(f"Error in handle_callback: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /name command: set or change player display name with validation."""
        try:
            player_id = str(update.effective_user.id)
            player_manager = self.game_manager.player_manager
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /name <new_name> ✏️\nChoose a new display name for your profile.")
                )
                return
            new_name = " ".join(args).strip()
            # Validation: length, allowed characters, uniqueness
            if len(new_name) < 3 or len(new_name) > 20:
                await self.send_message(
                    update,
                    self.formatter.bold("Name must be between 3 and 20 characters.")
                )
                return
            if not new_name.replace(" ", "").isalnum():
                await self.send_message(
                    update,
                    self.formatter.bold("Name can only contain letters, numbers, and spaces.")
                )
                return
            # Check uniqueness (optional, can be removed if not needed)
            all_players = player_manager.get_all_players()
            if any(p.get('name', '').lower() == new_name.lower() for p in all_players):
                await self.send_message(
                    update,
                    self.formatter.bold("That name is already taken. Please choose another.")
                )
                return
            # Update player name
            player = player_manager.get_player(player_id)
            if not player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            player['name'] = new_name
            player_manager.upsert_player(player)
            await self.send_message(
                update,
                self.formatter.bold(f"Your name has been updated to: {new_name} ✨")
            )
        except Exception as e:
            logger.error(f"Error in handle_name: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chat command: send a message to global chat with validation and broadcast."""
        try:
            player_id = str(update.effective_user.id)
            chat_manager = self.chat_manager
            player_manager = self.game_manager.player_manager
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /chat <message> 💬\nSend a message to global chat.")
                )
                return
            message = " ".join(args).strip()
            # Validation: length, allowed characters, spam prevention
            if len(message) < 1 or len(message) > 200:
                await self.send_message(
                    update,
                    self.formatter.bold("Message must be between 1 and 200 characters.")
                )
                return
            # Optionally, add more validation here
            player = player_manager.get_player(player_id)
            if not player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            name = player.get('name', f"Player_{player_id[:8]}")
            chat_manager.add_message(player_id, name, message)
            await self.send_message(
                update,
                self.formatter.bold("Message sent to global chat! 💬")
            )
            # Optionally, broadcast to all players (simulate global chat)
            # for p in player_manager.get_all_players():
            #     if p['player_id'] != player_id:
            #         # send message to each player (implement as needed)
        except Exception as e:
            logger.error(f"Error in handle_chat: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_block(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /block command: block another player from interacting with you."""
        try:
            player_id = str(update.effective_user.id)
            player_manager = self.game_manager.player_manager
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /block <player_name_or_id> 🚫\nBlock a player from interacting with you.")
                )
                return
            target = " ".join(args).strip()
            if target == player_id:
                await self.send_message(
                    update,
                    self.formatter.bold("You cannot block yourself.")
                )
                return
            # Find target by name or id
            all_players = player_manager.get_all_players()
            target_player = next((p for p in all_players if p.get('name', '').lower() == target.lower() or p['player_id'] == target), None)
            if not target_player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found.")
                )
                return
            # Add to block list (store in player['blocked'] as a set)
            player = player_manager.get_player(player_id)
            if not player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            blocked = set(player.get('blocked', []))
            if target_player['player_id'] in blocked:
                await self.send_message(
                    update,
                    self.formatter.bold("Player is already blocked.")
                )
                return
            blocked.add(target_player['player_id'])
            player['blocked'] = list(blocked)
            player_manager.upsert_player(player)
            await self.send_message(
                update,
                self.formatter.bold(f"You have blocked {target_player.get('name', target_player['player_id'])} 🚫")
            )
        except Exception as e:
            logger.error(f"Error in handle_block: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_unblock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unblock command: unblock a previously blocked player."""
        try:
            player_id = str(update.effective_user.id)
            player_manager = self.game_manager.player_manager
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /unblock <player_name_or_id> ✅\nUnblock a player.")
                )
                return
            target = " ".join(args).strip()
            # Find target by name or id
            all_players = player_manager.get_all_players()
            target_player = next((p for p in all_players if p.get('name', '').lower() == target.lower() or p['player_id'] == target), None)
            if not target_player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found.")
                )
                return
            player = player_manager.get_player(player_id)
            if not player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            blocked = set(player.get('blocked', []))
            if target_player['player_id'] not in blocked:
                await self.send_message(
                    update,
                    self.formatter.bold("Player is not blocked.")
                )
                return
            blocked.remove(target_player['player_id'])
            player['blocked'] = list(blocked)
            player_manager.upsert_player(player)
            await self.send_message(
                update,
                self.formatter.bold(f"You have unblocked {target_player.get('name', target_player['player_id'])} ✅")
            )
        except Exception as e:
            logger.error(f"Error in handle_unblock: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_level(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /level command: show current level, XP, and progress to next level."""
        try:
            player_manager = self.game_manager.player_manager
            progression_manager = self.game_manager.progression_manager if hasattr(self.game_manager, 'progression_manager') else None
            args = context.args
            if args:
                # View another player's level by name or ID
                target = " ".join(args).strip()
                all_players = player_manager.get_all_players()
                target_player = next((p for p in all_players if p.get('name', '').lower() == target.lower() or p['player_id'] == target), None)
                if not target_player:
                    await self.send_message(
                        update,
                        self.formatter.bold("Player not found.")
                    )
                    return
                player = target_player
            else:
                player_id = str(update.effective_user.id)
                player = player_manager.get_player(player_id)
                if not player:
                    await self.send_message(
                        update,
                        self.formatter.bold("Player not found. Try /start first.")
                    )
                    return
            level = player.get('level', 1)
            xp = player.get('xp', 0)
            # Calculate XP needed for next level
            if progression_manager:
                next_xp = progression_manager.get_xp_for_level(level + 1)
            else:
                next_xp = 100 * level  # fallback formula
            progress = min(100, int((xp / next_xp) * 100)) if next_xp > 0 else 100
            bar = '█' * (progress // 10) + '░' * (10 - (progress // 10))
            name = player.get('name', f"Player_{player.get('player_id', '')[:8]}")
            message = (
                f"🏅 <b>{name}'s Level</b>\n"
                f"Level: <b>{level}</b>\n"
                f"XP: <b>{xp} / {next_xp}</b>\n"
                f"Progress: <b>{progress}%</b>\n"
                f"<code>{bar}</code>"
            )
            await self.send_message(update, message)
        except Exception as e:
            logger.error(f"Error in handle_level: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /skills command: show current skills, points, and allow allocation if relevant."""
        try:
            player_id = str(update.effective_user.id)
            player_manager = self.game_manager.player_manager
            # If you have a SkillManager, use it; otherwise, use player profile
            skill_manager = getattr(self.game_manager, 'skill_manager', None)
            player = player_manager.get_player(player_id)
            if not player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            # Example skill structure: {'strength': 2, 'agility': 1, 'intellect': 0}
            skills = player.get('skills', {'strength': 0, 'agility': 0, 'intellect': 0})
            skill_points = player.get('skill_points', 0)
            sections = [{
                'title': 'Your Skills 🧠',
                'items': []
            }]
            for skill, value in skills.items():
                sections[0]['items'].append({
                    'type': 'skill',
                    'name': skill.capitalize(),
                    'description': f"Level: {value}",
                    'emoji': '✨',
                })
            message = self.format_message("Skills Menu", sections)
            message += f"\nSkill Points Available: <b>{skill_points}</b>"
            await self.send_message(update, message)
        except Exception as e:
            logger.error(f"Error in handle_skills: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_prestige(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /prestige command: show prestige status and allow prestige reset if eligible."""
        try:
            player_id = str(update.effective_user.id)
            player_manager = self.game_manager.player_manager
            progression_manager = self.game_manager.progression_manager if hasattr(self.game_manager, 'progression_manager') else None
            player = player_manager.get_player(player_id)
            if not player:
                await self.send_message(
                    update,
                    self.formatter.bold("Player not found. Try /start first.")
                )
                return
            prestige_level = player.get('prestige', 0)
            level = player.get('level', 1)
            can_prestige = level >= 100  # Example: must reach level 100 to prestige
            message = (
                f"🌟 <b>Prestige Status</b>\n"
                f"Current Prestige: <b>{prestige_level}</b>\n"
                f"Current Level: <b>{level}</b>\n"
            )
            if can_prestige:
                message += "\nYou are eligible to prestige! Use /prestige confirm to reset your progress for a permanent bonus."
            else:
                message += "\nReach level 100 to unlock prestige."
            # Handle confirmation
            args = context.args
            if args and args[0].lower() == 'confirm' and can_prestige:
                # Reset player progress, increase prestige, grant bonus
                player['prestige'] = prestige_level + 1
                player['level'] = 1
                player['xp'] = 0
                player['resources'] = {}
                player['skills'] = {'strength': 0, 'agility': 0, 'intellect': 0}
                player['skill_points'] = 0
                # Optionally, grant a permanent bonus (e.g., +5% XP per prestige)
                player['prestige_bonus'] = player.get('prestige_bonus', 0) + 5
                player_manager.upsert_player(player)
                message = (
                    f"🌟 <b>Prestige Complete!</b>\n"
                    f"You are now Prestige <b>{player['prestige']}</b>!\n"
                    f"You received a permanent +5% XP bonus."
                )
            await self.send_message(update, message)
        except Exception as e:
            logger.error(f"Error in handle_prestige: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /shop command: show available shop items and allow purchase."""
        try:
            player_id = str(update.effective_user.id)
            shop_manager = self.game_manager.shop_manager
            resource_manager = self.game_manager.resource_manager
            items = shop_manager.get_shop_items(player_id)
            player_resources = resource_manager.get_resources(player_id)
            if not items:
                await self.send_message(
                    update,
                    self.formatter.bold("No items available in the shop! 🏪")
                )
                return
            sections = [{
                'title': 'Shop 🏪',
                'items': []
            }]
            keyboard = []
            for item in items:
                cost_str = ', '.join(f"{k}: {v}" for k, v in item['cost'].items())
                can_afford = resource_manager.can_afford(player_id, item['cost'])
                desc = f"{item.get('emoji', '🏪')} <b>{item['name']}</b>\n{item['description']}\nCost: {cost_str}"
                sections[0]['items'].append({
                    'type': 'shop_item',
                    'name': item['name'],
                    'description': desc,
                    'emoji': item.get('emoji', '🏪'),
                })
                if can_afford:
                    keyboard.append([
                        {'text': f"Buy {item['name']}", 'callback_data': f"shop_buy_{item['id']}"}
                    ])
                else:
                    keyboard.append([
                        {'text': f"❌ Not enough resources for {item['name']}", 'callback_data': 'noop'}
                    ])
            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Shop Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_shop: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_bag(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bag command: show player inventory and allow item usage."""
        try:
            player_id = str(update.effective_user.id)
            bag_manager = self.game_manager.bag_manager
            items = bag_manager.get_bag_items(player_id)
            if not items:
                await self.send_message(
                    update,
                    self.formatter.bold("Your bag is empty! 🎒")
                )
                return
            sections = [{
                'title': 'Your Bag 🎒',
                'items': []
            }]
            keyboard = []
            for item in items:
                desc = f"{item.get('emoji', '🎒')} <b>{item['name']}</b>\n{item['description']}\nQuantity: {item['quantity']}"
                sections[0]['items'].append({
                    'type': 'bag_item',
                    'name': item['name'],
                    'description': desc,
                    'emoji': item.get('emoji', '🎒'),
                })
                keyboard.append([
                    {'text': f"Use {item['name']}", 'callback_data': f"bag_use_{item['id']}"}
                ])
            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Bag Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_bag: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_blackmarket(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /blackmarket command: show available black market items and allow purchase."""
        try:
            player_id = str(update.effective_user.id)
            black_market_manager = self.game_manager.black_market_manager
            resource_manager = self.game_manager.resource_manager
            items = black_market_manager.get_black_market_items(player_id)
            player_resources = resource_manager.get_resources(player_id)
            if not items:
                await self.send_message(
                    update,
                    self.formatter.bold("No items available in the black market! 🏪")
                )
                return
            sections = [{
                'title': 'Black Market 🏪',
                'items': []
            }]
            keyboard = []
            for item in items:
                cost_str = ', '.join(f"{k}: {v}" for k, v in item['cost'].items())
                can_afford = resource_manager.can_afford(player_id, item['cost'])
                desc = f"{item.get('emoji', '🏪')} <b>{item['name']}</b>\n{item['description']}\nCost: {cost_str}"
                sections[0]['items'].append({
                    'type': 'black_market_item',
                    'name': item['name'],
                    'description': desc,
                    'emoji': item.get('emoji', '🏪'),
                })
                if can_afford:
                    keyboard.append([
                        {'text': f"Buy {item['name']}", 'callback_data': f"blackmarket_buy_{item['id']}"}
                    ])
                else:
                    keyboard.append([
                        {'text': f"❌ Not enough resources for {item['name']}", 'callback_data': 'noop'}
                    ])
            keyboard.append([{'text': '🔙 Back', 'callback_data': 'status'}])
            message = self.format_message("Black Market Menu", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_blackmarket: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command: allow players to configure game settings like notifications, language, and other preferences."""
        try:
            player_id = update.effective_user.id
            settings = self.game_manager.player_manager.get_settings(player_id)
            if not settings:
                await self.send_message(
                    update,
                    self.formatter.bold("Settings not found. Please try again later. ⚙️")
                )
                return
            sections = [{
                'title': 'Game Settings ⚙️',
                'items': [
                    {
                        'type': 'setting',
                        'name': 'Notifications',
                        'value': 'Enabled' if settings.get('notifications', True) else 'Disabled',
                        'description': 'Receive game notifications'
                    },
                    {
                        'type': 'setting',
                        'name': 'Language',
                        'value': settings.get('language', 'English'),
                        'description': 'Game language'
                    },
                    {
                        'type': 'setting',
                        'name': 'Theme',
                        'value': settings.get('theme', 'Default'),
                        'description': 'Game theme'
                    },
                    {
                        'type': 'setting',
                        'name': 'Sound',
                        'value': 'Enabled' if settings.get('sound', True) else 'Disabled',
                        'description': 'Game sound effects'
                    },
                    {
                        'type': 'setting',
                        'name': 'Vibration',
                        'value': 'Enabled' if settings.get('vibration', True) else 'Disabled',
                        'description': 'Game vibration'
                    }
                ]
            }]
            keyboard = [
                [{'text': '🔔 Notifications', 'callback_data': 'settings_notifications'}],
                [{'text': '🌐 Language', 'callback_data': 'settings_language'}],
                [{'text': '🎨 Theme', 'callback_data': 'settings_theme'}],
                [{'text': '🔊 Sound', 'callback_data': 'settings_sound'}],
                [{'text': '📳 Vibration', 'callback_data': 'settings_vibration'}],
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            message = self.format_message("Settings", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_settings: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feedback command: allow players to submit feedback, bug reports, or suggestions."""
        try:
            sections = [{
                'title': 'Feedback 📝',
                'items': [
                    {
                        'type': 'text',
                        'text': 'We value your feedback! Please use the buttons below to submit your thoughts, report bugs, or suggest new features.'
                    }
                ]
            }]
            keyboard = [
                [{'text': '🐛 Report Bug', 'callback_data': 'feedback_bug'}],
                [{'text': '💡 Suggest Feature', 'callback_data': 'feedback_feature'}],
                [{'text': '📝 General Feedback', 'callback_data': 'feedback_general'}],
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            message = self.format_message("Feedback", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_feedback: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command: display information about the game, version, and credits."""
        try:
            sections = [{
                'title': 'About SkyHustle 🎮',
                'items': [
                    {
                        'type': 'text',
                        'text': 'SkyHustle is a Telegram-based strategy game where you build your empire, train armies, and conquer the world!'
                    },
                    {
                        'type': 'text',
                        'text': 'Version: 1.0.0'
                    },
                    {
                        'type': 'text',
                        'text': 'Developed by: Your Name'
                    },
                    {
                        'type': 'text',
                        'text': 'Special thanks to all our players and contributors!'
                    }
                ]
            }]
            keyboard = [[{'text': '🔙 Back', 'callback_data': 'status'}]]
            message = self.format_message("About", sections)
            await self.send_message(update, message, keyboard=keyboard)
        except Exception as e:
            logger.error(f"Error in handle_about: {e}", exc_info=True)
            await self._handle_error(update, e)