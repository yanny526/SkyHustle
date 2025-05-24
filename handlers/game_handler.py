"""
Main game handler for SkyHustle 2
Manages the Telegram bot interface and game state
"""

import time
import logging
import asyncio
from typing import Dict, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Import all managers
from modules.player_manager import PlayerManager
from modules.tutorial_manager import TutorialManager
from modules.resource_manager import ResourceManager
from modules.building_manager import BuildingManager
from modules.unit_manager import UnitManager
from modules.research_manager import ResearchManager
from modules.combat_manager import CombatManager
from modules.alliance_manager import AllianceManager
from modules.quest_manager import QuestManager
from modules.market_manager import MarketManager
from modules.achievement_manager import AchievementManager
from modules.daily_rewards_manager import DailyRewardsManager
from modules.social_manager import SocialManager
from modules.progression_manager import ProgressionManager
from modules.event_manager import EventManager

# Import all configurations
from config.game_config import (
    RESOURCES, BUILDINGS, UNITS, RESEARCH, QUESTS, ACHIEVEMENTS,
    DAILY_REWARDS, EVENTS, COMBAT, ALLIANCE_SETTINGS, QUEST_SETTINGS,
    QUEST_TYPES, QUEST_REWARDS, MARKET_SETTINGS, MARKET_EVENTS,
    GAME_SETTINGS, RESEARCH_TYPES, RESEARCH_REWARDS, BUILDING_UPGRADES,
    UNIT_UPGRADES, LEAGUE_REWARDS, ALLIANCE_PERKS, ALLIANCE_RANKS
)

# Set up logging
logger = logging.getLogger(__name__)

class GameHandler:
    def __init__(self):
        try:
            # Initialize core managers
            self.player_manager = PlayerManager()
            self.tutorial_manager = TutorialManager()
            self.resource_manager = ResourceManager()
            self.building_manager = BuildingManager()
            self.unit_manager = UnitManager()
            self.research_manager = ResearchManager()
            self.combat_manager = CombatManager()
            self.alliance_manager = AllianceManager()
            self.quest_manager = QuestManager()
            self.market_manager = MarketManager()
            self.achievement_manager = AchievementManager()
            self.daily_rewards_manager = DailyRewardsManager()
            self.social_manager = SocialManager()
            self.progression_manager = ProgressionManager()
            self.event_manager = EventManager()
            
            # Initialize state
            self.last_update = time.time()
            self.active_events = {}
            self.achievements = set()
            self.last_battle_time = {}
            self._update_task = None
            self._is_running = False
            
            logger.info("GameHandler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GameHandler: {e}", exc_info=True)
            raise

    async def start(self):
        """Start the game handler's background tasks"""
        if self._is_running:
            return
        
        self._is_running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("GameHandler background tasks started")

    async def stop(self):
        """Stop the game handler's background tasks"""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("GameHandler background tasks stopped")

    async def _update_loop(self):
        """Background update loop"""
        while self._is_running:
            try:
                await self.update()
                await asyncio.sleep(1)  # Update every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command with a lively, engaging UI"""
        try:
            player_id = str(update.effective_user.id)
            if not self.player_manager.get_player(player_id):
                result = self.player_manager.create_player(player_id)
                if not result['success']:
                    await update.message.reply_text("❌ Error creating player profile!")
                    return
                tutorial_result = self.tutorial_manager.start_tutorial(player_id)
                if tutorial_result['success']:
                    self.resource_manager.add_resources(player_id, self.tutorial_manager.starter_bonuses['resources'])
                    for building_id, level in self.tutorial_manager.starter_bonuses['buildings'].items():
                        self.building_manager.build_building(player_id, building_id, level)
                    for unit_id, count in self.tutorial_manager.starter_bonuses['units'].items():
                        self.unit_manager.train_units(player_id, unit_id, count)
            self.player_manager.update_last_login(player_id)
            current_step = self.tutorial_manager.get_current_step(player_id)
            
            # Welcome message with escaped special characters
            message = (
                "🎉 *Welcome to* _SkyHustle 2_\\! 🎮\n\n"
                "*Your adventure begins now\\!*\n"
                "Use /help or tap the button below to see what you can do\\!\n\n"
            )
            
            # Add tutorial step message if available
            if current_step:
                # Escape special characters in the tutorial message
                tutorial_message = current_step.get('message', 'Welcome to the game\\!')
                tutorial_message = tutorial_message.replace('!', '\\!').replace('.', '\\.').replace('-', '\\-')
                message += f"📚 *Current Tutorial Step:*\n{tutorial_message}\n\n"
            
            message += "🔥 _Tip: Invite friends for special rewards\\!_"
            
            # Create keyboard with main menu options
            keyboard = [
                [
                    InlineKeyboardButton("📊 Status", callback_data="status"),
                    InlineKeyboardButton("🏗️ Build", callback_data="build")
                ],
                [
                    InlineKeyboardButton("⚔️ Train", callback_data="train"),
                    InlineKeyboardButton("🎯 Attack", callback_data="attack")
                ],
                [
                    InlineKeyboardButton("📚 Tutorial", callback_data="tutorial"),
                    InlineKeyboardButton("❓ Help", callback_data="help")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_start: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def _handle_error(self, update: Update, error: Exception):
        """Handle errors in command handlers"""
        error_message = "An error occurred. Please try again later."
        
        if isinstance(error, TelegramError):
            error_message = "Telegram API error. Please try again later."
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}", exc_info=True)

    def update(self):
        """Update game state"""
        try:
            current_time = time.time()
            time_passed = current_time - self.last_update
            self.last_update = current_time
            
            # Update resources for all players
            for player in self.player_manager.get_all_players():
                self.resource_manager.update_resources(player['player_id'])
            
            # Update building upgrades
            self.building_manager.update_upgrades()
            
            # Update unit training
            self.unit_manager.update_training()
            
            # Update research
            self.research_manager.update_research()
            
            # Update events
            self._update_events()
            
            # Update quests
            self.quest_manager.check_quest_expiration()
            
            # Update market listings
            self.market_manager.get_market_listings()
            
            # Update market events
            self.market_manager.get_active_events()
            
            # Update alliance wars
            self._update_alliance_wars()
            
        except Exception as e:
            logger.error(f"Error in update: {e}", exc_info=True)

    def _update_events(self):
        """Update active events"""
        try:
            current_time = time.time()
            expired_events = []
            
            for event_id, event in self.active_events.items():
                if current_time >= event['end_time']:
                    expired_events.append(event_id)
            
            for event_id in expired_events:
                del self.active_events[event_id]
                
        except Exception as e:
            logger.error(f"Error in _update_events: {e}", exc_info=True)

    def _update_alliance_wars(self):
        """Update alliance wars"""
        try:
            current_time = time.time()
            active_wars = self.alliance_manager.get_active_wars()
            
            for war in active_wars:
                if current_time >= war['end_time']:
                    self.alliance_manager.end_war(war['id'])
                    
        except Exception as e:
            logger.error(f"Error in _update_alliance_wars: {e}", exc_info=True)

    def get_daily_attack_suggestions(self, player_id: str) -> list:
        """Suggest 5 players to attack daily"""
        try:
            # Get all player IDs
            all_players = [p['player_id'] for p in self.player_manager.get_all_players()]
            # Exclude self
            all_players = [pid for pid in all_players if pid != player_id]
            
            # Get player's alliance
            player_alliance = self.alliance_manager.get_player_alliance(player_id)
            if player_alliance and player_alliance.get('success'):
                # Exclude same alliance members
                alliance_members = player_alliance['alliance']['members']
                all_players = [pid for pid in all_players if pid not in alliance_members]
            
            # Only include active players (logged in within last 7 days)
            now = time.time()
            active_players = [pid for pid in all_players if self.player_manager.get_player(pid) and self.player_manager.get_player(pid).get('last_login', 0) > now - 7*86400]
            
            # If not enough, fallback to all_players
            candidates = active_players if len(active_players) >= 5 else all_players
            
            # Sort by level difference (closest to player)
            my_level = self.player_manager.get_player(player_id)['level'] if self.player_manager.get_player(player_id) else 1
            candidates.sort(key=lambda pid: abs(self.player_manager.get_player(pid)['level'] - my_level) if self.player_manager.get_player(pid) else 100)
            
            # Pick up to 5
            suggestions = candidates[:5]
            
            # Return as list of dicts with name and level
            return [
                {
                    'id': pid,
                    'name': self.player_manager.get_player_name(pid),
                    'level': self.player_manager.get_player(pid)['level'] if self.player_manager.get_player(pid) else 1
                }
                for pid in suggestions
            ]
        except Exception as e:
            logger.error(f"Error in get_daily_attack_suggestions: {e}", exc_info=True)
            return []

    async def handle_help(self, update, context):
        """Handle the /help command with enhanced UI"""
        try:
            message = (
                "❓ *Help Center* ❓\n\n"
                "Welcome to SkyHustle 2! Here's how to get started:\n\n"
                "🎮 *Basic Commands:*\n"
                "└ /start - Begin your adventure\n"
                "└ /status - Check your current status\n"
                "└ /help - Show this help message\n"
                "└ /tutorial - Start the tutorial\n\n"
                "🏰 *Game Features:*\n"
                "└ /build - Manage your buildings\n"
                "└ /train - Train your army\n"
                "└ /market - Trade with other players\n"
                "└ /alliance - Join or manage alliances\n"
                "└ /social - Connect with friends\n\n"
                "📊 *Game Systems:*\n"
                "└ /inventory - Manage your items\n"
                "└ /events - View active events\n"
                "└ /leaderboard - Check rankings\n"
                "└ /settings - Configure game settings\n\n"
                "Need more help? Select a category below:"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🎮 Gameplay", callback_data="help_gameplay"),
                    InlineKeyboardButton("🏰 Buildings", callback_data="help_buildings")
                ],
                [
                    InlineKeyboardButton("⚔️ Combat", callback_data="help_combat"),
                    InlineKeyboardButton("💰 Economy", callback_data="help_economy")
                ],
                [
                    InlineKeyboardButton("🤝 Social", callback_data="help_social"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="help_settings")
                ],
                [
                    InlineKeyboardButton("❓ FAQ", callback_data="help_faq"),
                    InlineKeyboardButton("📝 Support", callback_data="help_support")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_help: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_status(self, update, context):
        """Handle the /status command"""
        try:
            player_id = str(update.effective_user.id)
            level = self.progression_manager.get_player_level(player_id)
            xp = self.progression_manager.get_player_xp(player_id)
            hustlecoins = self.player_manager.get_hustlecoins(player_id)
            resources = self.resource_manager.get_resources(player_id)
            buildings = self.building_manager.get_buildings(player_id)
            army = self.unit_manager.get_army(player_id)

            # Enhanced status message with better formatting and emojis
            message = (
                "🏰 *Your SkyHustle Base* 🏰\n\n"
                f"👤 *Player Status*\n"
                f"└ Level: {level}  ✨ XP: {xp}  💎 HustleCoins: {hustlecoins}\n\n"
                "🌲 *Resources*\n"
            )
            
            # Resource display with progress bars
            for k, v in resources.items():
                max_capacity = self.resource_manager.get_max_capacity(player_id, k)
                percentage = (v / max_capacity) * 100
                progress_bar = self._create_progress_bar(percentage)
                message += f"└ {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {v}/{max_capacity} {progress_bar}\n"
            
            message += "\n🏗️ *Buildings*\n"
            if buildings:
                for k, v in buildings.items():
                    message += f"└ {BUILDINGS[k]['emoji']} {BUILDINGS[k]['name']}: Lv{v}\n"
            else:
                message += "└ No buildings constructed yet\n"
            
            message += "\n⚔️ *Army*\n"
            if army:
                for k, v in army.items():
                    message += f"└ {UNITS[k]['emoji']} {UNITS[k]['name']}: {v}\n"
            else:
                message += "└ No units trained yet\n"

            # Enhanced keyboard layout with better organization
            keyboard = [
                [
                    InlineKeyboardButton("🏗️ Build", callback_data="build"),
                    InlineKeyboardButton("⚔️ Train", callback_data="train")
                ],
                [
                    InlineKeyboardButton("🎯 Quest", callback_data="quest"),
                    InlineKeyboardButton("🏪 Market", callback_data="market")
                ],
                [
                    InlineKeyboardButton("👥 Profile", callback_data="profile"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_status: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _create_progress_bar(self, percentage: float) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"[{'█' * filled}{'░' * empty}] {percentage:.1f}%"

    async def handle_profile(self, update, context):
        """Show player profile with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            player = self.player_manager.get_player(player_id)
            if not player:
                await update.message.reply_text("❌ Player not found. Use /start to begin.")
                return

            # Get player stats
            level = self.progression_manager.get_player_level(player_id)
            xp = self.progression_manager.get_player_xp(player_id)
            next_level_xp = self.progression_manager.get_next_level_xp(player_id)
            progress = self.progression_manager.get_level_progress(player_id)
            achievements = self.achievement_manager.get_player_achievements(player_id)
            
            # Enhanced profile message with better formatting
            message = (
                "👤 *Player Profile*\n\n"
                f"*Name:* {player.get('name', 'Unknown')}\n"
                f"*Level:* {level}  ✨ *XP:* {xp}/{next_level_xp}\n"
                f"*Progress:* {self._create_progress_bar(progress['progress_percentage'])}\n\n"
            )

            # Add achievements section
            if achievements.get('achievements'):
                message += "🏆 *Recent Achievements*\n"
                for achievement in achievements['achievements'][-3:]:  # Show last 3 achievements
                    message += f"└ {achievement['emoji']} {achievement['name']}\n"
                message += "\n"

            # Add stats section
            message += "📊 *Stats*\n"
            stats = {
                "Buildings": len(player.get('buildings', {})),
                "Units": sum(player.get('army', {}).values()),
                "Wars Won": player.get('wars_won', 0),
                "Quests Completed": player.get('quests_completed', 0)
            }
            for stat, value in stats.items():
                message += f"└ {stat}: {value}\n"

            # Enhanced keyboard layout
            keyboard = [
                [
                    InlineKeyboardButton("🏆 Achievements", callback_data="achievements"),
                    InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")
                ],
                [
                    InlineKeyboardButton("👥 Friends", callback_data="friends"),
                    InlineKeyboardButton("🤝 Alliance", callback_data="alliance")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_profile: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_name(self, update, context):
        """Set or change player name."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Please provide a name. Usage: /name <your_name>")
                return
            name = " ".join(context.args)
            if not (3 <= len(name) <= 20) or not name.replace(' ', '').isalnum():
                await update.message.reply_text("Name must be 3-20 characters, letters/numbers/spaces only.")
                return
            result = self.player_manager.set_player_name(player_id, name)
            if result.get('success'):
                await update.message.reply_text(f"✅ Your name has been set to: {name}")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not set name.')}")
        except Exception as e:
            logger.error(f"Error in handle_name: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_leaderboard(self, update, context):
        """Handle the /leaderboard command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            
            # Get leaderboard categories
            categories = {
                'level': 'Level',
                'power': 'Power',
                'buildings': 'Buildings',
                'units': 'Units',
                'wars_won': 'Wars Won',
                'quests_completed': 'Quests Completed'
            }
            
            # Get current category from context or default to level
            current_category = context.args[0] if context.args else 'level'
            if current_category not in categories:
                current_category = 'level'
            
            # Get leaderboard data
            leaderboard = self.player_manager.get_leaderboard(current_category)
            
            message = (
                "🏆 *Leaderboard* 🏆\n\n"
                f"📊 *{categories[current_category]} Rankings*\n\n"
            )
            
            # Display top players
            for i, player in enumerate(leaderboard[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                value = self._format_leaderboard_value(current_category, player)
                message += (
                    f"{medal} {i}. {player['name']}\n"
                    f"└ {value}\n"
                    f"└ Level: {player['level']} | XP: {player['xp']}\n\n"
                )
            
            # Display player's rank if not in top 10
            player_rank = self.player_manager.get_player_rank(player_id, current_category)
            if player_rank > 10:
                player_data = self.player_manager.get_player(player_id)
                value = self._format_leaderboard_value(current_category, player_data)
                message += (
                    f"📌 *Your Rank:* #{player_rank}\n"
                    f"└ {value}\n"
                    f"└ Level: {player_data['level']} | XP: {player_data['xp']}\n\n"
                )
            
            # Create keyboard for category selection
            keyboard = []
            for category, name in categories.items():
                keyboard.append([
                    InlineKeyboardButton(
                        f"{'✅' if category == current_category else '📊'} {name}",
                        callback_data=f"leaderboard_{category}"
                    )
                ])
            
            # Add navigation buttons
            keyboard.extend([
                [
                    InlineKeyboardButton("👤 My Profile", callback_data="profile"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_leaderboard: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _format_leaderboard_value(self, category: str, player: dict) -> str:
        """Format leaderboard value based on category"""
        if category == 'level':
            return f"Level {player['level']}"
        elif category == 'power':
            return f"Power: {player.get('power', 0)} ⚔️"
        elif category == 'buildings':
            return f"Buildings: {len(player.get('buildings', {}))} 🏗️"
        elif category == 'units':
            return f"Units: {sum(player.get('army', {}).values())} ⚔️"
        elif category == 'wars_won':
            return f"Wars Won: {player.get('wars_won', 0)} 🏰"
        elif category == 'quests_completed':
            return f"Quests: {player.get('quests_completed', 0)} 🎯"
        return "N/A"

    async def handle_achievements(self, update, context):
        """Show player's achievements with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            result = self.achievement_manager.get_player_achievements(player_id)
            if not result['success']:
                await update.message.reply_text("❌ Could not fetch achievements.", parse_mode='MarkdownV2')
                return
            achievements = result['achievements']
            if not achievements:
                await update.message.reply_text("No achievements yet. Start playing to earn some! 🥇", parse_mode='MarkdownV2')
                return
            message = "🥇 *Your Achievements* 🥇\n\n"
            for ach in achievements:
                status = "✅" if ach['completed'] else "❌"
                emoji = ach.get('emoji', '🏆')
                message += f"{status} {emoji} *{ach['name']}*: {ach['description']}\n"
            keyboard = [
                [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"), InlineKeyboardButton("👤 Profile", callback_data="profile")],
                [InlineKeyboardButton("🔙 Back", callback_data="status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_achievements: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_friends(self, update, context):
        """Show and manage friends with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            friends = self.social_manager.get_friend_list(player_id)
            if not friends:
                await update.message.reply_text("You have no friends yet. Use /add_friend <player_id> to add one! 👥", parse_mode='MarkdownV2')
                return
            message = "👥 *Your Friends* 👥\n\n"
            for f in friends:
                name = f.get('player_id', 'Unknown')
                online = "🟢" if f.get('online') else "⚪"
                last_seen = f.get('last_seen', 0)
                last_seen_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(last_seen)) if last_seen else 'N/A'
                message += f"{online} {name} (Last seen: {last_seen_str})\n"
            keyboard = [
                [InlineKeyboardButton("➕ Add Friend", callback_data="add_friend"), InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
                [InlineKeyboardButton("🔙 Back", callback_data="status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_friends: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_chat(self, update, context):
        """Show and manage chat."""
        try:
            player_id = str(update.effective_user.id)
            # For simplicity, just show a placeholder
            await update.message.reply_text("Chat feature coming soon!")
        except Exception as e:
            logger.error(f"Error in handle_chat: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_level(self, update, context):
        """Show player's level and progress."""
        try:
            player_id = str(update.effective_user.id)
            player = self.player_manager.get_player(player_id)
            if not player:
                await update.message.reply_text("❌ Player not found. Use /start to begin.")
                return
            level = player.get('level', 1)
            xp = player.get('xp', 0)
            message = f"Level: {level}\nXP: {xp}"
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error in handle_level: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_skills(self, update, context):
        """Show player's skills."""
        try:
            player_id = str(update.effective_user.id)
            player = self.player_manager.get_player(player_id)
            skills = player.get('skills', {}) if player else {}
            if isinstance(skills, str):
                import json
                try:
                    skills = json.loads(skills)
                    if not isinstance(skills, dict):
                        skills = {}
                except Exception:
                    skills = {}
            elif not isinstance(skills, dict):
                skills = {}
            if not skills:
                await update.message.reply_text("No skills found. Unlock skills as you progress!")
                return
            message = "*Your Skills:*\n\n"
            for skill, value in skills.items():
                message += f"*{skill}:* {value}\n"
            await update.message.reply_text(message, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_skills: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_prestige(self, update, context):
        """Show or manage prestige."""
        try:
            player_id = str(update.effective_user.id)
            player = self.player_manager.get_player(player_id)
            prestige = player.get('prestige', 0) if player else 0
            message = f"Your Prestige Level: {prestige}\n(Prestige system coming soon!)"
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error in handle_prestige: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_create_alliance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle alliance creation"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args or len(context.args) < 2:
                await update.message.reply_text("Usage: /create_alliance <name> <description> 🤝", parse_mode='MarkdownV2')
                return
            name = context.args[0]
            description = ' '.join(context.args[1:])
            result = self.alliance_manager.create_alliance(player_id, name, description)
            if result.get('success'):
                await update.message.reply_text(f"✅ Alliance *{name}* created! Welcome to the world of alliances! 🤝", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not create alliance.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_create_alliance: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_join_alliance(self, update, context):
        """Join an alliance with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /join_alliance <alliance_id> 🤝", parse_mode='MarkdownV2')
                return
            alliance_id = context.args[0]
            result = self.alliance_manager.join_alliance(player_id, alliance_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Joined alliance {alliance_id}! Welcome to your new team! 🤝", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not join alliance.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_join_alliance: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_chat(self, update, context):
        """Show alliance chat with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_player_alliance(player_id)
            if not alliance:
                await update.message.reply_text("You are not in an alliance. 🤝", parse_mode='MarkdownV2')
                return
            chat = self.alliance_manager.get_chat_history(alliance['alliance_id'])
            if not chat:
                await update.message.reply_text("No messages in alliance chat yet. 💬", parse_mode='MarkdownV2')
                return
            message = "💬 *Alliance Chat* 💬\n\n" + "\n".join(f"{msg['player_id']}: {msg['message']}" for msg in chat)
            keyboard = [[InlineKeyboardButton("✏️ Send Message", callback_data="send_alliance_message")], [InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_chat: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_donate(self, update, context):
        """Donate resources to alliance with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args or len(context.args) < 2:
                await update.message.reply_text("Usage: /alliance_donate <alliance_id> <resource>:<amount> ... 🎁", parse_mode='MarkdownV2')
                return
            alliance_id = context.args[0]
            resources = {}
            for arg in context.args[1:]:
                if ':' in arg:
                    res, amt = arg.split(':', 1)
                    try:
                        resources[res] = int(amt)
                    except ValueError:
                        continue
            result = self.alliance_manager.donate_resources(player_id, alliance_id, resources)
            if result.get('success'):
                await update.message.reply_text(f"✅ Donated to alliance {alliance_id}! Your generosity is legendary! 🎁", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not donate resources.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_donate: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_war(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle alliance war declaration"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_war <target_alliance_id> ⚔️", parse_mode='MarkdownV2')
                return
            target_alliance_id = context.args[0]
            result = self.alliance_manager.declare_war(player_id, target_alliance_id)
            if result.get('success'):
                await update.message.reply_text(f"⚔️ War declared on alliance {target_alliance_id}! Let the battles begin! ⚔️", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not declare war.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_war: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_peace(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle alliance peace declaration"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_peace <target_alliance_id> 🕊️", parse_mode='MarkdownV2')
                return
            target_alliance_id = context.args[0]
            result = self.alliance_manager.declare_peace(player_id, target_alliance_id)
            if result.get('success'):
                await update.message.reply_text(f"🕊️ Peace declared with alliance {target_alliance_id}\! May prosperity follow\! 🕊️", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not declare peace.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_peace: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_manage(self, update, context):
        """Show alliance management options with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_player_alliance(player_id)
            if not alliance:
                await update.message.reply_text("You are not in an alliance. 🤝", parse_mode='MarkdownV2')
                return
            message = f"🛠️ *Alliance Management for {alliance['name']}* 🛠️\n\n(Management features coming soon!)"
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_manage: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_list(self, update, context):
        """List all alliances with lively UI"""
        try:
            alliances = self.alliance_manager.get_all_alliances()
            if not alliances:
                await update.message.reply_text("No alliances found. 🤝", parse_mode='MarkdownV2')
                return
            message = "🤝 *Alliances* 🤝\n" + "\n".join(f"{a['name']} (ID: {a['alliance_id']})" for a in alliances)
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_list: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _escape_markdown(self, text: str) -> str:
        """Helper method to escape special characters for MarkdownV2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    async def handle_alliance_info(self, update, context):
        """Show alliance info with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_alliance_info(player_id)
            if not alliance:
                await update.message.reply_text("You are not in an alliance. 🤝", parse_mode='MarkdownV2')
                return
            message = (
                f"🤝 *Alliance Info* 🤝\n"
                f"*Name:* {self._escape_markdown(alliance['name'])}\n"
                f"*Level:* {alliance.get('level', 1)}\n"
                f"*Leader:* {self._escape_markdown(alliance.get('leader', 'Unknown'))}\n"
                f"*Members:* {self._escape_markdown(', '.join(alliance.get('members', [])))}\n"
                f"*Description:* {self._escape_markdown(alliance.get('description', ''))}"
            )
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_info: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_promote(self, update, context):
        """Promote a member in the alliance with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_promote <member_id> ⬆️", parse_mode='MarkdownV2')
                return
            member_id = context.args[0]
            result = self.alliance_manager.promote_member(player_id, member_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Promoted member {member_id}! ⬆️", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not promote member.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_promote: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_demote(self, update, context):
        """Demote a member in the alliance with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_demote <member_id> ⬇️", parse_mode='MarkdownV2')
                return
            member_id = context.args[0]
            result = self.alliance_manager.demote_member(player_id, member_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Demoted member {member_id}! ⬇️", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not demote member.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_demote: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_transfer(self, update, context):
        """Transfer alliance leadership with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_transfer <new_leader_id> 👑", parse_mode='MarkdownV2')
                return
            new_leader_id = context.args[0]
            result = self.alliance_manager.transfer_leadership(player_id, new_leader_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Leadership transferred to {new_leader_id}! 👑", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not transfer leadership.')}", parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_transfer: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_requests(self, update, context):
        """Show join requests for the alliance with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            requests = self.alliance_manager.get_join_requests(player_id)
            if not requests:
                await update.message.reply_text("No join requests found. 🤝", parse_mode='MarkdownV2')
                return
            message = "📨 *Join Requests* 📨\n" + "\n".join(f"{r['player_id']}" for r in requests)
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_requests: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_war_rankings(self, update, context):
        """Show alliance war rankings with lively UI"""
        try:
            rankings = self.alliance_manager.get_alliance_rankings()
            if not rankings:
                await update.message.reply_text("No alliance war rankings available. ⚔️", parse_mode='MarkdownV2')
                return
            message = "⚔️ *Alliance War Rankings* ⚔️\n\n"
            for i, alliance in enumerate(rankings[:10], 1):
                message += (
                    f"{i}. *{self._escape_markdown(alliance['name'])}*\n"
                    f"  Wins: {alliance['wins']}\n"
                    f"  Losses: {alliance['losses']}\n"
                    f"  Points: {alliance['points']}\n\n"
                )
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_war_rankings: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_benefits(self, update, context):
        """Show alliance benefits with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            benefits = self.alliance_manager.get_alliance_benefits(player_id)
            if not benefits:
                await update.message.reply_text("No alliance benefits found. 🎁", parse_mode='MarkdownV2')
                return
            message = "🎁 *Alliance Benefits* 🎁\n\n"
            for k, v in benefits.items():
                message += f"└ *{k}*\n"
                message += f"  {v}\n\n"
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_benefits: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_resources(self, update, context):
        """Show alliance resources with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            resources = self.alliance_manager.get_alliance_resources(player_id)
            if isinstance(resources, str):
                import json
                try:
                    resources = json.loads(resources)
                    if not isinstance(resources, dict):
                        resources = {}
                except Exception:
                    resources = {}
            elif not isinstance(resources, dict):
                resources = {}
            if not resources:
                await update.message.reply_text("No alliance resources found. 🤝", parse_mode='MarkdownV2')
                return
            message = "💰 *Alliance Resources* 💰\n\n"
            for k, v in resources.items():
                message += f"└ {self._get_resource_emoji(k)} {k}: {v}\n"
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_resources: {e}", exc_info=True)
            await self._handle_error(update, e)
    async def handle_alliance_research(self, update, context):
        """Show alliance research with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            research = self.alliance_manager.get_alliance_research(player_id)
            if not research:
                await update.message.reply_text("No alliance research found. 🔬", parse_mode='MarkdownV2')
                return
            message = "🔬 *Alliance Research* 🔬\n\n"
            for r in research:
                message += (
                    f"└ *{self._escape_markdown(r['name'])}*\n"
                    f"  Level: {r['level']}\n"
                    f"  {self._escape_markdown(r.get('description', ''))}\n\n"
                )
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_research: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_diplomacy(self, update, context):
        """Show alliance diplomacy status with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            diplomacy = self.alliance_manager.get_alliance_diplomacy(player_id)
            if not diplomacy:
                await update.message.reply_text("No alliance diplomacy data found. 🤝", parse_mode='MarkdownV2')
                return
            message = "🤝 *Alliance Diplomacy* 🤝\n\n"
            for d in diplomacy:
                message += f"└ *{d['target']}*\n"
                message += f"  Status: {d['status']}\n"
                message += f"  Points: {d['points']}\n\n"
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance_diplomacy: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_build(self, update, context):
        """Handle the /build command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            buildings = self.building_manager.get_available_buildings(player_id)
            resources = self.resource_manager.get_resources(player_id)
            
            message = (
                "🏗️ *Construction Site* 🏗️\n\n"
                "🌲 *Your Resources:*\n"
            )
            
            # Display current resources
            for k, v in resources.items():
                message += f"└ {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {v}\n"
            
            message += "\n🏛️ *Available Buildings:*\n"
            keyboard = []
            
            for building in buildings:
                # Get building requirements
                reqs = self.building_manager.get_building_requirements(building['id'])
                current_level = self.building_manager.get_building_level(player_id, building['id'])
                
                # Format requirements with emojis
                req_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in reqs.items())
                
                message += (
                    f"└ {BUILDINGS[building['id']]['emoji']} *{self._escape_markdown(building['name'])}*\n"
                    f"  Level: {current_level}\n"
                    f"  {self._escape_markdown(building['description'])}\n"
                    f"  💰 Cost: {req_str}\n\n"
                )
                
                # Add build button if requirements met
                can_build = all(resources.get(k, 0) >= v for k, v in reqs.items())
                button_text = f"🏗️ Build {building['name']}" if can_build else f"❌ {building['name']} (Requirements not met)"
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"build_{building['id']}"
                    )
                ])
            
            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_build"),
                InlineKeyboardButton("🔙 Back", callback_data="status")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_build: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _get_resource_emoji(self, resource: str) -> str:
        """Get emoji for resource type"""
        emojis = {
            'gold': '💰',
            'wood': '🪵',
            'stone': '🪨',
            'food': '🍖',
            'hustlecoins': '💎',
            'gems': '💎',
            'energy': '⚡',
            'experience': '✨'
        }
        return emojis.get(resource, '❓')

    async def handle_train(self, update, context):
        """Handle the /train command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            units = self.unit_manager.get_available_units(player_id)
            resources = self.resource_manager.get_resources(player_id)
            
            message = (
                "⚔️ *Training Grounds* ⚔️\n\n"
                "🌲 *Your Resources:*\n"
            )
            
            # Display current resources
            for k, v in resources.items():
                message += f"└ {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {v}\n"
            
            message += "\n👥 *Available Units:*\n"
            keyboard = []
            
            for unit in units:
                # Get unit requirements and stats
                reqs = self.unit_manager.get_unit_requirements(unit['id'])
                stats = self.unit_manager.get_unit_stats(unit['id'])
                current_count = self.unit_manager.get_unit_count(player_id, unit['id'])
                
                # Format requirements with emojis
                req_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in reqs.items())
                
                # Format stats
                stats_str = " | ".join(f"{k}: {v}" for k, v in stats.items())
                
                message += (
                    f"└ {UNITS[unit['id']]['emoji']} *{unit['name']}*\n"
                    f"  Count: {current_count}\n"
                    f"  {unit['description']}\n"
                    f"  ⚔️ Stats: {stats_str}\n"
                    f"  💰 Cost: {req_str}\n\n"
                )
                
                # Add train button if requirements met
                can_train = all(resources.get(k, 0) >= v for k, v in reqs.items())
                button_text = f"⚔️ Train {unit['name']}" if can_train else f"❌ {unit['name']} (Requirements not met)"
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"train_{unit['id']}"
                    )
                ])
            
            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_train"),
                InlineKeyboardButton("🔙 Back", callback_data="status")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_train: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_quest(self, update, context):
        """Handle the /quest command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            quests = self.quest_manager.get_available_quests(player_id)
            active_quests = self.quest_manager.get_active_quests(player_id)
            
            message = (
                "🎯 *Quest Board* 🎯\n\n"
            )
            
            # Display active quests
            if active_quests:
                message += "⚡ *Active Quests:*\n"
                for quest in active_quests:
                    progress = self.quest_manager.get_quest_progress(player_id, quest['id'])
                    progress_bar = self._create_progress_bar(progress['percentage'])
                    
                    message += (
                        f"└ {QUEST_TYPES[quest['type']]['emoji']} *{quest['name']}*\n"
                        f"  {quest['description']}\n"
                        f"  📊 Progress: {progress['current']}/{progress['target']} {progress_bar}\n"
                        f"  🎁 Rewards: {self._format_rewards(quest['rewards'])}\n\n"
                    )
            else:
                message += "No active quests. Start a new one below!\n\n"
            
            # Display available quests
            message += "📜 *Available Quests:*\n"
            keyboard = []
            
            for quest in quests:
                message += (
                    f"└ {QUEST_TYPES[quest['type']]['emoji']} *{quest['name']}*\n"
                    f"  {quest['description']}\n"
                    f"  ⏱️ Duration: {quest['duration']} minutes\n"
                    f"  🎁 Rewards: {self._format_rewards(quest['rewards'])}\n\n"
                )
                
                # Add start quest button
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎯 Start {quest['name']}",
                        callback_data=f"quest_start_{quest['id']}"
                    )
                ])
            
            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_quest"),
                InlineKeyboardButton("🔙 Back", callback_data="status")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_quest: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _format_rewards(self, rewards: dict) -> str:
        """Format quest rewards with emojis"""
        reward_strs = []
        for k, v in rewards.items():
            if k in RESOURCES:
                reward_strs.append(f"{RESOURCES[k]['emoji']} {v}")
            elif k == 'xp':
                reward_strs.append(f"✨ {v} XP")
            elif k == 'hustlecoins':
                reward_strs.append(f"💎 {v} HustleCoins")
        return " | ".join(reward_strs)

    async def handle_research(self, update, context):
        """Handle the /research command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            research = self.research_manager.get_available_research(player_id)
            active_research = self.research_manager.get_active_research(player_id)
            resources = self.resource_manager.get_resources(player_id)
            
            message = (
                "🔬 *Research Lab* 🔬\n\n"
                "🌲 *Your Resources:*\n"
            )
            
            # Display current resources
            for k, v in resources.items():
                message += f"└ {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {v}\n"
            
            # Display active research
            if active_research:
                message += "\n⚡ *Active Research:*\n"
                for tech in active_research:
                    progress = self.research_manager.get_research_progress(player_id, tech['id'])
                    progress_bar = self._create_progress_bar(progress['percentage'])
                    
                    message += (
                        f"└ {RESEARCH_TYPES[tech['type']]['emoji']} *{tech['name']}*\n"
                        f"  {tech['description']}\n"
                        f"  📊 Progress: {progress['current']}/{progress['target']} {progress_bar}\n"
                        f"  ⏱️ Time Remaining: {progress['time_remaining']} minutes\n\n"
                    )
            
            # Display available research
            message += "\n📚 *Available Research:*\n"
            keyboard = []
            
            for tech in research:
                # Get research requirements
                reqs = self.research_manager.get_research_requirements(tech['id'])
                current_level = self.research_manager.get_research_level(player_id, tech['id'])
                
                # Format requirements with emojis
                req_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in reqs.items())
                
                message += (
                    f"└ {RESEARCH_TYPES[tech['type']]['emoji']} *{tech['name']}*\n"
                    f"  Level: {current_level}\n"
                    f"  {tech['description']}\n"
                    f"  💰 Cost: {req_str}\n"
                    f"  🎁 Benefits: {self._format_research_benefits(tech['benefits'])}\n\n"
                )
                
                # Add research button if requirements met
                can_research = all(resources.get(k, 0) >= v for k, v in reqs.items())
                button_text = f"🔬 Research {tech['name']}" if can_research else f"❌ {tech['name']} (Requirements not met)"
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"research_{tech['id']}"
                    )
                ])
            
            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_research"),
                InlineKeyboardButton("🔙 Back", callback_data="status")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_research: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _format_research_benefits(self, benefits: dict) -> str:
        """Format research benefits with emojis"""
        benefit_strs = []
        for k, v in benefits.items():
            if k == 'production':
                benefit_strs.append(f"📈 +{v}% Production")
            elif k == 'efficiency':
                benefit_strs.append(f"⚡ +{v}% Efficiency")
            elif k == 'capacity':
                benefit_strs.append(f"📦 +{v}% Capacity")
            elif k == 'combat':
                benefit_strs.append(f"⚔️ +{v}% Combat Power")
        return " | ".join(benefit_strs)

    async def handle_combat(self, update, context):
        """Handle the /combat command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            army = self.unit_manager.get_army(player_id)
            suggestions = self.get_daily_attack_suggestions(player_id)
            
            message = (
                "⚔️ *Combat Center* ⚔️\n\n"
                "👥 *Your Army:*\n"
            )
            
            # Display current army
            if army:
                total_power = sum(UNITS[unit_id]['power'] * count for unit_id, count in army.items())
                message += f"└ Total Power: {total_power} ⚔️\n"
                for unit_id, count in army.items():
                    message += f"└ {UNITS[unit_id]['emoji']} {UNITS[unit_id]['name']}: {count} (Power: {UNITS[unit_id]['power'] * count})\n"
            else:
                message += "└ No units available for combat\n"
            
            # Display suggested targets
            if suggestions:
                message += "\n🎯 *Suggested Targets:*\n"
                keyboard = []
                for target in suggestions:
                    message += (
                        f"└ 👤 {target['name']} (Level {target['level']})\n"
                        f"  ⚔️ Estimated Power: {self.combat_manager.estimate_power(target['id'])}\n"
                        f"  🏆 Win Rate: {self.combat_manager.calculate_win_rate(player_id, target['id'])}%\n\n"
                    )
                    keyboard.append([
                        InlineKeyboardButton(
                            f"⚔️ Attack {target['name']}",
                            callback_data=f"combat_attack_{target['id']}"
                        )
                    ])
            else:
                message += "\nNo suitable targets found. Try again later!\n"
            
            # Add combat options
            message += "\n⚡ *Combat Options:*\n"
            keyboard.extend([
                [
                    InlineKeyboardButton("🔄 Refresh Targets", callback_data="combat_refresh"),
                    InlineKeyboardButton("📊 Battle History", callback_data="combat_history")
                ],
                [
                    InlineKeyboardButton("🏆 Rankings", callback_data="combat_rankings"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_combat: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_battle_result(self, update, context):
        """Handle battle results with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            target_id = query.data.split('_')[-1]
            
            # Get battle result
            result = self.combat_manager.process_battle(player_id, target_id)
            
            # Format battle report
            message = (
                "⚔️ *Battle Report* ⚔️\n\n"
                f"🏰 *Attacker:* {self.player_manager.get_player_name(player_id)}\n"
                f"🎯 *Target:* {self.player_manager.get_player_name(target_id)}\n\n"
            )
            
            # Battle details
            message += "📊 *Battle Details:*\n"
            message += f"└ Your Power: {result['attacker_power']} ⚔️\n"
            message += f"└ Enemy Power: {result['defender_power']} ⚔️\n"
            message += f"└ Battle Duration: {result['duration']} seconds\n\n"
            
            # Casualties
            message += "💀 *Casualties:*\n"
            for unit_id, count in result['attacker_losses'].items():
                message += f"└ {UNITS[unit_id]['emoji']} {UNITS[unit_id]['name']}: -{count}\n"
            
            # Rewards
            if result['victory']:
                message += "\n🎁 *Rewards:*\n"
                for resource, amount in result['rewards'].items():
                    message += f"└ {self._get_resource_emoji(resource)} {amount}\n"
            
            # Battle outcome
            message += f"\n{'🏆 Victory!' if result['victory'] else '❌ Defeat!'}\n"
            
            keyboard = [
                [InlineKeyboardButton("⚔️ Attack Again", callback_data=f"combat_attack_{target_id}")],
                [InlineKeyboardButton("🔄 New Target", callback_data="combat_refresh")],
                [InlineKeyboardButton("🔙 Back", callback_data="status")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_battle_result: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance(self, update, context):
        """Handle the /alliance command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_player_alliance(player_id)
            
            if alliance:
                # Player is in an alliance
                message = (
                    "🤝 *Alliance Headquarters* 🤝\n\n"
                    f"🏰 *{alliance['name']}*\n"
                    f"└ Level: {alliance.get('level', 1)}\n"
                    f"└ Members: {len(alliance.get('members', []))}/{ALLIANCE_SETTINGS['max_members']}\n"
                    f"└ Description: {alliance.get('description', 'No description')}\n\n"
                )
                
                # Display alliance resources
                resources = self.alliance_manager.get_alliance_resources(player_id)
                if resources:
                    message += "💰 *Alliance Resources:*\n"
                    for k, v in resources.items():
                        message += f"└ {self._get_resource_emoji(k)} {v}\n"
                
                # Display alliance perks
                perks = self.alliance_manager.get_alliance_perks(player_id)
                if perks:
                    message += "\n✨ *Active Perks:*\n"
                    for perk in perks:
                        message += f"└ {perk['emoji']} {perk['name']}: {perk['description']}\n"
                
                # Display recent activities
                activities = self.alliance_manager.get_recent_activities(player_id)
                if activities:
                    message += "\n📜 *Recent Activities:*\n"
                    for activity in activities[:5]:  # Show last 5 activities
                        message += f"└ {activity['emoji']} {activity['description']}\n"
                
                # Create keyboard based on player's role
                keyboard = []
                if alliance.get('leader') == player_id:
                    # Leader options
                    keyboard.extend([
                        [InlineKeyboardButton("👥 Manage Members", callback_data="alliance_manage")],
                        [InlineKeyboardButton("⚔️ Declare War", callback_data="alliance_war")],
                        [InlineKeyboardButton("🤝 Diplomacy", callback_data="alliance_diplomacy")]
                    ])
                elif alliance.get('officers', []).count(player_id) > 0:
                    # Officer options
                    keyboard.extend([
                        [InlineKeyboardButton("👥 View Members", callback_data="alliance_members")],
                        [InlineKeyboardButton("⚔️ War Status", callback_data="alliance_war_status")]
                    ])
                else:
                    # Member options
                    keyboard.extend([
                        [InlineKeyboardButton("👥 View Members", callback_data="alliance_members")],
                        [InlineKeyboardButton("🎁 Donate", callback_data="alliance_donate")]
                    ])
                
                # Common options for all members
                keyboard.extend([
                    [
                        InlineKeyboardButton("💬 Chat", callback_data="alliance_chat"),
                        InlineKeyboardButton("📊 Stats", callback_data="alliance_stats")
                    ],
                    [
                        InlineKeyboardButton("🔄 Refresh", callback_data="alliance_refresh"),
                        InlineKeyboardButton("🔙 Back", callback_data="status")
                    ]
                ])
            else:
                # Player is not in an alliance
                message = (
                    "🤝 *Alliance Center* 🤝\n\n"
                    "Join or create an alliance to unlock powerful benefits!\n\n"
                    "*Alliance Benefits:*\n"
                    "└ 🛡️ Alliance Protection\n"
                    "└ 💰 Resource Sharing\n"
                    "└ ⚔️ Alliance Wars\n"
                    "└ 🎁 Special Perks\n"
                )
                
                # Show available alliances
                alliances = self.alliance_manager.get_all_alliances()
                if alliances:
                    message += "\n🏰 *Available Alliances:*\n"
                    for alliance in alliances[:5]:  # Show top 5 alliances
                        message += (
                            f"└ {alliance['name']}\n"
                            f"  Level: {alliance.get('level', 1)}\n"
                            f"  Members: {len(alliance.get('members', []))}/{ALLIANCE_SETTINGS['max_members']}\n\n"
                        )
                
                keyboard = [
                    [InlineKeyboardButton("➕ Create Alliance", callback_data="alliance_create")],
                    [InlineKeyboardButton("🔍 Browse Alliances", callback_data="alliance_browse")],
                    [InlineKeyboardButton("🔙 Back", callback_data="status")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_alliance: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_market(self, update, context):
        """Handle the /market command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            resources = self.resource_manager.get_resources(player_id)
            listings = self.market_manager.get_market_listings()
            active_events = self.market_manager.get_active_events()
            
            message = (
                "🏪 *Marketplace* 🏪\n\n"
                "💰 *Your Resources:*\n"
            )
            
            # Display current resources
            for k, v in resources.items():
                message += f"└ {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {v}\n"
            
            # Display active market events
            if active_events:
                message += "\n⚡ *Active Events:*\n"
                for event in active_events:
                    message += (
                        f"└ {event['emoji']} *{event['name']}*\n"
                        f"  {event['description']}\n"
                        f"  ⏱️ Ends in: {event['time_remaining']}\n\n"
                    )
            
            # Display market listings
            if listings:
                message += "📊 *Current Listings:*\n"
                keyboard = []
                for listing in listings:
                    # Format resources with emojis
                    offer_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in listing['offer'].items())
                    request_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in listing['request'].items())
                    
                    message += (
                        f"└ 👤 {self.player_manager.get_player_name(listing['seller_id'])}\n"
                        f"   Offers: {offer_str}\n"
                        f"  🔄 Wants: {request_str}\n\n"
                    )
                    
                    # Add trade button if player has requested resources
                    can_trade = all(resources.get(k, 0) >= v for k, v in listing['request'].items())
                    button_text = f"🔄 Trade" if can_trade else "❌ Can't Trade"
                    keyboard.append([
                        InlineKeyboardButton(
                            button_text,
                            callback_data=f"market_trade_{listing['id']}"
                        )
                    ])
            else:
                message += "\nNo active listings in the market.\n"
            
            # Add market options
            message += "\n⚡ *Market Options:*\n"
            keyboard.extend([
                [
                    InlineKeyboardButton("➕ Create Listing", callback_data="market_create"),
                    InlineKeyboardButton("📊 My Listings", callback_data="market_my_listings")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="market_refresh"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_market: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_market_trade(self, update, context):
        """Handle market trade with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            listing_id = query.data.split('_')[-1]
            
            # Get listing details
            listing = self.market_manager.get_listing(listing_id)
            if not listing:
                await query.answer("Listing no longer available!")
                return
            
            # Process trade
            result = self.market_manager.process_trade(player_id, listing_id)
            
            # Format trade result message
            message = (
                "🔄 *Trade Result* 🔄\n\n"
                f"👤 *Seller:* {self._escape_markdown(self.player_manager.get_player_name(listing['seller_id']))}\n"
                f"👤 *Buyer:* {self._escape_markdown(self.player_manager.get_player_name(player_id))}\n\n"
            )
            
            if result['success']:
                # Format traded resources
                offer_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in listing['offer'].items())
                request_str = " | ".join(f"{self._get_resource_emoji(k)} {v}" for k, v in listing['request'].items())
                
                message += (
                    "✅ *Trade Successful!*\n\n"
                    f"💰 *You Received:* {offer_str}\n"
                    f"💸 *You Paid:* {request_str}\n"
                )
            else:
                message += f"❌ *Trade Failed:* {result['message']}\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 New Trade", callback_data="market_refresh")],
                [InlineKeyboardButton("🔙 Back", callback_data="status")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_market_trade: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_social(self, update, context):
        """Handle the /social command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            friends = self.social_manager.get_friend_list(player_id)
            friend_requests = self.social_manager.get_friend_requests(player_id)
            recent_activities = self.social_manager.get_recent_activities(player_id)
            
            message = (
                "👥 *Social Hub* 👥\n\n"
            )
            
            # Display friend requests
            if friend_requests:
                message += "📨 *Friend Requests:*\n"
                keyboard = []
                for request in friend_requests:
                    message += (
                        f"└ 👤 {self.player_manager.get_player_name(request['sender_id'])}\n"
                        f"  Level: {self.progression_manager.get_player_level(request['sender_id'])}\n\n"
                    )
                    keyboard.extend([
                        [
                            InlineKeyboardButton(
                                f"✅ Accept {request['sender_id']}",
                                callback_data=f"social_accept_{request['sender_id']}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"❌ Decline {request['sender_id']}",
                                callback_data=f"social_decline_{request['sender_id']}"
                            )
                        ]
                    ])
            
            # Display friends list
            if friends:
                message += "\n🤝 *Your Friends:*\n"
                for friend in friends:
                    online = "🟢" if friend.get('online') else "⚪"
                    last_seen = time.strftime('%Y-%m-%d %H:%M', time.localtime(friend.get('last_seen', 0)))
                    level = self.progression_manager.get_player_level(friend['player_id'])
                    
                    message += (
                        f"└ {online} {self.player_manager.get_player_name(friend['player_id'])}\n"
                        f"  Level: {level}\n"
                        f"  Last seen: {last_seen}\n\n"
                    )
            else:
                message += "\nNo friends yet. Add some friends to get started!\n"
            
            # Display recent activities
            if recent_activities:
                message += "\n📜 *Recent Activities:*\n"
                for activity in recent_activities[:5]:  # Show last 5 activities
                    message += f"└ {activity['emoji']} {activity['description']}\n"
            
            # Add social options
            message += "\n⚡ *Social Options:*\n"
            keyboard.extend([
                [
                    InlineKeyboardButton("➕ Add Friend", callback_data="social_add"),
                    InlineKeyboardButton("👥 Find Players", callback_data="social_find")
                ],
                [
                    InlineKeyboardButton("🎁 Send Gift", callback_data="social_gift"),
                    InlineKeyboardButton("💬 Chat", callback_data="social_chat")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="social_refresh"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_social: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_social_gift(self, update, context):
        """Handle sending gifts to friends with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            friend_id = query.data.split('_')[-1]
            
            # Get player's resources
            resources = self.resource_manager.get_resources(player_id)
            
            message = (
                "🎁 *Send Gift* 🎁\n\n"
                f"👤 *Recipient:* {self.player_manager.get_player_name(friend_id)}\n\n"
                "💰 *Your Resources:*\n"
            )
            
            # Display available resources
            keyboard = []
            for k, v in resources.items():
                message += f"└ {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {v}\n"
                if v > 0:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🎁 Send {RESOURCES[k]['name']}",
                            callback_data=f"social_gift_{friend_id}_{k}"
                        )
                    ])
            
            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton("🔙 Back", callback_data="social")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_social_gift: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_tutorial(self, update, context):
        """Handle the /tutorial command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            current_step = self.tutorial_manager.get_current_step(player_id)
            completed_steps = self.tutorial_manager.get_completed_steps(player_id)
            
            message = (
                "📚 *Tutorial Center* 📚\n\n"
            )
            
            # Display current step
            if current_step:
                message += (
                    "🎯 *Current Step:*\n"
                    f"└ {current_step['emoji']} *{current_step['name']}*\n"
                    f"  {current_step['description']}\n\n"
                )
                
                # Display step requirements
                if current_step.get('requirements'):
                    message += "📋 *Requirements:*\n"
                    for req in current_step['requirements']:
                        message += f"└ {req['emoji']} {req['description']}\n"
                    message += "\n"
                
                # Display step rewards
                if current_step.get('rewards'):
                    message += "🎁 *Rewards:*\n"
                    for reward in current_step['rewards']:
                        message += f"└ {reward['emoji']} {reward['description']}\n"
                    message += "\n"
            else:
                message += "🎉 *Tutorial Completed!*\n\n"
            
            # Display progress
            total_steps = len(self.tutorial_manager.tutorial_steps)
            progress = len(completed_steps) / total_steps * 100
            progress_bar = self._create_progress_bar(progress)
            
            message += (
                "📊 *Progress:*\n"
                f"└ Completed: {len(completed_steps)}/{total_steps} steps\n"
                f"└ {progress_bar}\n\n"
            )
            
            # Display completed steps
            if completed_steps:
                message += "✅ *Completed Steps:*\n"
                for step in completed_steps[-3:]:  # Show last 3 completed steps
                    message += f"└ {step['emoji']} {step['name']}\n"
            
            # Create keyboard
            keyboard = []
            if current_step:
                keyboard.append([
                    InlineKeyboardButton(
                        "🎯 Start Current Step",
                        callback_data=f"tutorial_start_{current_step['id']}"
                    )
                ])
            
            keyboard.extend([
                [
                    InlineKeyboardButton("📖 View All Steps", callback_data="tutorial_steps"),
                    InlineKeyboardButton("❓ Help", callback_data="tutorial_help")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="tutorial_refresh"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_tutorial: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_tutorial_step(self, update, context):
        """Handle tutorial step completion with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            step_id = query.data.split('_')[-1]
            
            # Process step completion
            result = self.tutorial_manager.complete_step(player_id, step_id)
            
            # Format completion message
            message = (
                "🎯 *Tutorial Step Complete!* 🎯\n\n"
            )
            
            if result['success']:
                step = result['step']
                message += (
                    f"✅ *{step['name']}*\n"
                    f"{step['description']}\n\n"
                )
                
                # Display rewards
                if result.get('rewards'):
                    message += "🎁 *Rewards Earned:*\n"
                    for reward in result['rewards']:
                        message += f"└ {reward['emoji']} {reward['description']}\n"
                
                # Display next step
                if result.get('next_step'):
                    next_step = result['next_step']
                    message += (
                        "\n📚 *Next Step:*\n"
                        f"└ {next_step['emoji']} *{next_step['name']}*\n"
                        f"  {next_step['description']}\n"
                    )
            else:
                message += f"❌ {result['message']}\n"
            
            keyboard = [
                [InlineKeyboardButton("🎯 Continue Tutorial", callback_data="tutorial")],
                [InlineKeyboardButton("🔙 Back", callback_data="status")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_tutorial_step: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_settings(self, update, context):
        """Handle the /settings command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            settings = self.player_manager.get_player_settings(player_id)
            
            message = (
                "⚙️ *Game Settings* ⚙️\n\n"
            )
            
            # Display notification settings
            message += "🔔 *Notifications:*\n"
            notification_settings = {
                'battle_alerts': 'Battle Alerts',
                'resource_alerts': 'Resource Alerts',
                'alliance_alerts': 'Alliance Alerts',
                'quest_alerts': 'Quest Alerts',
                'market_alerts': 'Market Alerts'
            }
            
            for key, name in notification_settings.items():
                status = "✅" if settings.get(key, True) else "❌"
                message += f"└ {status} {name}\n"
            
            # Display display settings
            message += "\n🎨 *Display Settings:*\n"
            display_settings = {
                'show_emojis': 'Show Emojis',
                'show_progress_bars': 'Show Progress Bars',
                'compact_mode': 'Compact Mode',
                'dark_mode': 'Dark Mode'
            }
            
            for key, name in display_settings.items():
                status = "✅" if settings.get(key, True) else "❌"
                message += f"└ {status} {name}\n"
            
            # Display game settings
            message += "\n🎮 *Game Settings:*\n"
            game_settings = {
                'auto_collect': 'Auto-Collect Resources',
                'auto_train': 'Auto-Train Units',
                'auto_research': 'Auto-Research',
                'confirm_actions': 'Confirm Actions'
            }
            
            for key, name in game_settings.items():
                status = "✅" if settings.get(key, True) else "❌"
                message += f"└ {status} {name.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}\n"
            
            # Create keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
                    InlineKeyboardButton("🎨 Display", callback_data="settings_display")
                ],
                [
                    InlineKeyboardButton("🎮 Game", callback_data="settings_game"),
                    InlineKeyboardButton("🔒 Privacy", callback_data="settings_privacy")
                ],
                [
                    InlineKeyboardButton("🔄 Reset Settings", callback_data="settings_reset"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_settings: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_settings_update(self, update, context):
        """Handle settings updates with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            setting_type = query.data.split('_')[1]
            
            # Get current settings
            settings = self.player_manager.get_player_settings(player_id)
            
            # Create message based on setting type
            message = f"⚙️ *{setting_type.title()} Settings* ⚙️\n\n"
            keyboard = []
            
            if setting_type == 'notifications':
                for key, name in {
                    'battle_alerts': 'Battle Alerts',
                    'resource_alerts': 'Resource Alerts',
                    'alliance_alerts': 'Alliance Alerts',
                    'quest_alerts': 'Quest Alerts',
                    'market_alerts': 'Market Alerts'
                }.items():
                    status = "✅" if settings.get(key, True) else "❌"
                    message += f"└ {status} {name}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{'Disable' if settings.get(key, True) else 'Enable'} {name}",
                            callback_data=f"settings_toggle_{key}"
                        )
                    ])
            
            elif setting_type == 'display':
                for key, name in {
                    'show_emojis': 'Show Emojis',
                    'show_progress_bars': 'Show Progress Bars',
                    'compact_mode': 'Compact Mode',
                    'dark_mode': 'Dark Mode'
                }.items():
                    status = "✅" if settings.get(key, True) else "❌"
                    message += f"└ {status} {name}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{'Disable' if settings.get(key, True) else 'Enable'} {name}",
                            callback_data=f"settings_toggle_{key}"
                        )
                    ])
            
            elif setting_type == 'game':
                for key, name in {
                    'auto_collect': 'Auto-Collect Resources',
                    'auto_train': 'Auto-Train Units',
                    'auto_research': 'Auto-Research',
                    'confirm_actions': 'Confirm Actions'
                }.items():
                    status = "✅" if settings.get(key, True) else "❌"
                    message += f"└ {status} {name.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{'Disable' if settings.get(key, True) else 'Enable'} {name}",
                            callback_data=f"settings_toggle_{key}"
                        )
                    ])
            
            # Add navigation buttons
            keyboard.extend([
                [
                    InlineKeyboardButton("🔄 Reset to Default", callback_data=f"settings_reset_{setting_type}"),
                    InlineKeyboardButton("🔙 Back", callback_data="settings")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_settings_update: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_notifications(self, update, context):
        """Handle the /notifications command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            notifications = self.player_manager.get_notifications(player_id)
            
            message = (
                "🔔 *Notifications Center* 🔔\n\n"
            )
            
            # Display unread notifications
            unread = [n for n in notifications if not n.get('read', False)]
            if unread:
                message += "📨 *Unread Notifications:*\n"
                for notification in unread[:5]:  # Show last 5 unread
                    message += (
                        f"└ {notification['emoji']} *{notification['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}*\n"
                        f"  {notification['message'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}\n"
                        f"  ⏰ {time.strftime('%Y-%m-%d %H:%M', time.localtime(notification['timestamp']))}\n\n"
                    )
            else:
                message += "No unread notifications.\n\n"
            
            # Display recent notifications
            message += "📜 *Recent Notifications:*\n"
            for notification in notifications[-5:]:  # Show last 5 notifications
                read_status = "✅" if notification.get('read', False) else "📨"
                message += (
                    f"└ {read_status} {notification['emoji']} *{notification['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}*\n"
                    f"  {notification['message'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}\n"
                    f"  ⏰ {time.strftime('%Y-%m-%d %H:%M', time.localtime(notification['timestamp']))}\n\n"
                )
            
            # Create keyboard
            keyboard = [
                [
                    InlineKeyboardButton("📨 Mark All Read", callback_data="notifications_mark_all_read"),
                    InlineKeyboardButton("🗑️ Clear All", callback_data="notifications_clear_all")
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings_notifications"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_notifications: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_notification_action(self, update, context):
        """Handle notification actions with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            action = query.data.split('_')[1]
            
            if action == 'mark_all_read':
                self.player_manager.mark_all_notifications_read(player_id)
                message = "✅ All notifications marked as read!"
            elif action == 'clear_all':
                self.player_manager.clear_all_notifications(player_id)
                message = "🗑️ All notifications cleared!"
            else:
                message = "❌ Invalid action!"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Notifications", callback_data="notifications")],
                [InlineKeyboardButton("🔙 Back to Status", callback_data="status")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_notification_action: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_daily_rewards(self, update, context):
        """Handle the /daily command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            rewards = self.daily_rewards_manager.get_daily_rewards(player_id)
            streak = self.daily_rewards_manager.get_streak(player_id)
            
            message = (
                "🎁 *Daily Rewards* 🎁\n\n"
            )
            
            # Display current streak
            message += (
                "🔥 *Current Streak:*\n"
                f"└ {streak['current']} days (Best: {streak['best']})\n"
                f"└ {self._create_progress_bar(streak['next_bonus'])}\n\n"
            )
            
            # Display today's reward
            today = rewards['today']
            message += (
                "📅 *Today's Reward:*\n"
                f"└ {today['emoji']} *{today['name']}*\n"
                f"  {today['description']}\n"
                f"  🎁 {self._format_rewards(today['rewards'])}\n\n"
            )
            
            # Display streak bonuses
            message += "✨ *Streak Bonuses:*\n"
            for day, bonus in rewards['streak_bonuses'].items():
                message += (
                    f"└ Day {day}: {bonus['emoji']} {bonus['name']}\n"
                    f"  {bonus['description']}\n"
                    f"  🎁 {self._format_rewards(bonus['rewards'])}\n\n"
                )
            
            # Display next reward
            next_reward = rewards['next']
            message += (
                "⏳ *Next Reward:*\n"
                f"└ {next_reward['emoji']} *{next_reward['name']}*\n"
                f"  {next_reward['description']}\n"
                f"  🎁 {self._format_rewards(next_reward['rewards'])}\n"
                f"  ⏰ Available in: {next_reward['time_remaining']}\n\n"
            )
            
            # Create keyboard
            keyboard = []
            if rewards['can_claim']:
                keyboard.append([
                    InlineKeyboardButton(
                        "🎁 Claim Reward",
                        callback_data="daily_claim"
                    )
                ])
            
            keyboard.extend([
                [
                    InlineKeyboardButton("📅 Calendar", callback_data="daily_calendar"),
                    InlineKeyboardButton("📊 Stats", callback_data="daily_stats")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="daily_refresh"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_daily_rewards: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_daily_claim(self, update, context):
        """Handle daily reward claiming with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            
            # Process reward claim
            result = self.daily_rewards_manager.claim_reward(player_id)
            
            # Format claim message
            message = (
                "🎁 *Daily Reward Claimed!* 🎁\n\n"
            )
            
            if result['success']:
                message += (
                    f"✅ *{result['reward']['name']}*\n"
                    f"{result['reward']['description']}\n\n"
                )
                
                # Display rewards
                message += "🎁 *Rewards Earned:*\n"
                for reward in result['rewards']:
                    message += f"└ {reward['emoji']} {reward['description']}\n"
                
                # Display streak update
                if result.get('streak_updated'):
                    message += (
                        f"\n🔥 *Streak Updated:* {result['new_streak']} days\n"
                        f"└ {result['streak_message']}\n"
                    )
                
                # Display next reward
                next_reward = result['next_reward']
                message += (
                    f"\n⏳ *Next Reward:*\n"
                    f"└ {next_reward['emoji']} *{next_reward['name']}*\n"
                    f"  {next_reward['description']}\n"
                    f"  🎁 {self._format_rewards(next_reward['rewards'])}\n"
                    f"  ⏰ Available in: {next_reward['time_remaining']}\n"
                )
            else:
                message += f"❌ {result['message']}\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="daily_refresh")],
                [InlineKeyboardButton("🔙 Back", callback_data="status")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_daily_claim: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_event_leaderboard(self, update, context):
        """Handle event leaderboard with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            event_id = query.data.split('_')[-1]
            
            # Get event leaderboard
            leaderboard = self.event_manager.get_event_leaderboard(event_id)
            event = self.event_manager.get_event(event_id)
            
            message = (
                "🏆 *Event Leaderboard* 🏆\n\n"
                f"🎉 *{event['name']}*\n"
                f"{event['description']}\n\n"
            )
            
            # Display top players
            for i, player in enumerate(leaderboard[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                message += (
                    f"{medal} {i}. {player['name']}\n"
                    f"└ Score: {player['score']}\n"
                    f"└ Rewards: {self._format_rewards(player['rewards'])}\n\n"
                )
            
            # Display player's rank if not in top 10
            player_rank = self.event_manager.get_player_rank(player_id, event_id)
            if player_rank > 10:
                player_data = self.event_manager.get_player_event_data(player_id, event_id)
                message += (
                    f"📌 *Your Rank:* #{player_rank}\n"
                    f"└ Score: {player_data['score']}\n"
                    f"└ Rewards: {self._format_rewards(player_data['rewards'])}\n\n"
                )
            
            # Create keyboard
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data=f"events_leaderboard_{event_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data="events")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_event_leaderboard: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_inventory(self, update, context):
        """Handle the /inventory command with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            inventory = self.player_manager.get_inventory(player_id)
            
            message = (
                "🎒 *Inventory* 🎒\n\n"
            )
            
            # Display resources
            message += "💰 *Resources:*\n"
            for resource, amount in inventory['resources'].items():
                max_capacity = self.resource_manager.get_max_capacity(player_id, resource)
                percentage = (amount / max_capacity) * 100
                progress_bar = self._create_progress_bar(percentage)
                message += f"└ {RESOURCES[resource]['emoji']} {RESOURCES[resource]['name']}: {amount}/{max_capacity} {progress_bar}\n"
            
            # Display items
            if inventory['items']:
                message += "\n🎁 *Items:*\n"
                for item in inventory['items']:
                    message += (
                        f"└ {item['emoji']} *{item['name']}* (x{item['quantity']})\n"
                        f"  {item['description']}\n"
                        f"  🎯 Use: {item['use_description']}\n\n"
                    )
            else:
                message += "\nNo items in inventory.\n"
            
            # Display equipment
            if inventory['equipment']:
                message += "\n⚔️ *Equipment:*\n"
                for slot, item in inventory['equipment'].items():
                    message += (
                        f"└ {item['emoji']} *{item['name']}* ({slot.title()})\n"
                        f"  {item['description']}\n"
                        f"  📊 Stats: {self._format_equipment_stats(item['stats'])}\n\n"
                    )
            else:
                message += "\nNo equipment equipped.\n"
            
            # Display consumables
            if inventory['consumables']:
                message += "\n🧪 *Consumables:*\n"
                for item in inventory['consumables']:
                    message += (
                        f"└ {item['emoji']} *{item['name']}* (x{item['quantity']})\n"
                        f"  {item['description']}\n"
                        f"  ⚡ Effect: {item['effect_description']}\n\n"
                    )
            else:
                message += "\nNo consumables in inventory.\n"
            
            # Create keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🎁 Use Item", callback_data="inventory_use"),
                    InlineKeyboardButton("⚔️ Equip", callback_data="inventory_equip")
                ],
                [
                    InlineKeyboardButton("🧪 Consume", callback_data="inventory_consume"),
                    InlineKeyboardButton("🗑️ Discard", callback_data="inventory_discard")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="inventory_refresh"),
                    InlineKeyboardButton("🔙 Back", callback_data="status")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_inventory: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _format_equipment_stats(self, stats: dict) -> str:
        """Format equipment stats with emojis"""
        stat_emojis = {
            'attack': '⚔️',
            'defense': '🛡️',
            'speed': '⚡',
            'health': '❤️',
            'energy': '🔋',
            'luck': '🍀'
        }
        return " | ".join(f"{stat_emojis.get(k, '📊')} {v}" for k, v in stats.items())

    async def handle_inventory_action(self, update, context):
        """Handle inventory actions with enhanced UI"""
        try:
            query = update.callback_query
            player_id = str(query.from_user.id)
            action = query.data.split('_')[1]
            item_id = query.data.split('_')[-1]
            
            # Process inventory action
            result = self.player_manager.process_inventory_action(player_id, action, item_id)
            
            # Format action message
            message = (
                "🎒 *Inventory Action* 🎒\n\n"
            )
            
            if result['success']:
                message += (
                    f"✅ *{result['item']['name'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}*\n"
                    f"{result['item']['description'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')}\n\n"
                )
                
                # Display action result
                if action == 'use':
                    message += "🎯 *Effect:*\n"
                    for effect in result['effects']:
                        message += f"└ {effect['emoji']} {effect['description']}\n"
                elif action == 'equip':
                    message += "📊 *Stats Applied:*\n"
                    for stat, value in result['stats'].items():
                        message += f"└ {self._format_equipment_stats({stat: value})}\n"
                elif action == 'consume':
                    message += "⚡ *Effect:*\n"
                    message += f"└ {result['effect']['description']}\n"
                elif action == 'discard':
                    message += "🗑️ *Item discarded successfully*\n"
            else:
                message += f"❌ {result['message']}\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="inventory_refresh")],
                [InlineKeyboardButton("🔙 Back", callback_data="inventory")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_inventory_action: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_help_category(self, update, context):
        """Handle help category selection with enhanced UI"""
        try:
            query = update.callback_query
            category = query.data.split('_')[1]
            
            # Get help content for category
            help_content = self._get_help_content(category)
            
            message = (
                f"❓ *{help_content['title']}* ❓\n\n"
                f"{help_content['description']}\n\n"
            )
            
            # Add category-specific content
            for section in help_content['sections']:
                message += f"*{section['title']}*\n"
                for item in section['items']:
                    message += f"└ {item}\n"
                message += "\n"
            
            # Add tips if available
            if help_content.get('tips'):
                message += "*💡 Pro Tips:*\n"
                for tip in help_content['tips']:
                    message += f"└ {tip}\n"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Help", callback_data="help")],
                [InlineKeyboardButton("📝 Contact Support", callback_data="help_contact")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_help_category: {e}", exc_info=True)
            await self._handle_error(update, e)

    def _get_help_content(self, category: str) -> dict:
        """Get help content for a specific category"""
        help_content = {
            'gameplay': {
                'title': 'Gameplay Guide',
                'description': 'Learn the basics of SkyHustle 2 and how to progress efficiently.',
                'sections': [
                    {
                        'title': 'Getting Started',
                        'items': [
                            'Complete the tutorial to learn basic mechanics',
                            'Build your first resource buildings',
                            'Train your initial army units',
                            'Join an alliance for support'
                        ]
                    },
                    {
                        'title': 'Daily Activities',
                        'items': [
                            'Collect daily rewards',
                            'Complete daily quests',
                            'Participate in events',
                            'Trade in the market'
                        ]
                    }
                ],
                'tips': [
                    'Focus on resource production early game',
                    'Join an active alliance for better rewards',
                    'Save resources for important upgrades'
                ]
            },
            'buildings': {
                'title': 'Buildings Guide',
                'description': 'Master the art of city building and resource management.',
                'sections': [
                    {
                        'title': 'Resource Buildings',
                        'items': [
                            'Mines for gold production',
                            'Farms for food production',
                            'Lumber mills for wood production',
                            'Quarries for stone production'
                        ]
                    },
                    {
                        'title': 'Military Buildings',
                        'items': [
                            'Barracks for training troops',
                            'Archery ranges for ranged units',
                            'Stables for cavalry units',
                            'Siege workshops for siege weapons'
                        ]
                    }
                ],
                'tips': [
                    'Upgrade resource buildings evenly',
                    'Focus on military buildings during war',
                    'Keep your storage buildings upgraded'
                ]
            }
            # Add more categories as needed
        }
        
        return help_content.get(category, {
            'title': 'Help Category',
            'description': 'This help section is under construction.',
            'sections': []
        })

    async def handle_support(self, update, context):
        """Handle support requests with enhanced UI"""
        try:
            message = (
                "📝 *Support Center* 📝\n\n"
                "Need help? We're here for you!\n\n"
                "Select your issue type:"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🐛 Bug Report", callback_data="support_bug"),
                    InlineKeyboardButton("💡 Suggestion", callback_data="support_suggestion")
                ],
                [
                    InlineKeyboardButton("❓ Question", callback_data="support_question"),
                    InlineKeyboardButton("⚠️ Issue", callback_data="support_issue")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Help", callback_data="help")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_support: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_support_request(self, update, context):
        """Handle support request submission with enhanced UI"""
        try:
            query = update.callback_query
            request_type = query.data.split('_')[1]
            
            # Store request type in user context
            context.user_data['support_type'] = request_type
            
            message = (
                "📝 *Support Request* 📝\n\n"
                f"Please describe your {request_type} in detail:\n\n"
                "Include any relevant information such as:\n"
                "└ Steps to reproduce (for bugs)\n"
                "└ Expected vs actual behavior\n"
                "└ Screenshots if applicable\n"
                "└ Your game version\n\n"
                "Type your message below:"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="help")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_support_request: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_support_submit(self, update, context):
        """Handle support request submission with enhanced UI"""
        try:
            player_id = str(update.effective_user.id)
            request_type = context.user_data.get('support_type', 'general')
            message_text = update.message.text
            
            # Submit support request
            result = self.support_manager.submit_request(player_id, request_type, message_text)
            
            if result['success']:
                message = (
                    "✅ *Support Request Submitted* ✅\n\n"
                    f"Your {request_type} has been received.\n"
                    f"Ticket ID: {result['ticket_id']}\n\n"
                    "We'll review your request and get back to you soon.\n"
                    "You can check the status of your request in the support center."
                )
            else:
                message = (
                    "❌ *Error Submitting Request* ❌\n\n"
                    f"{result['message']}\n\n"
                    "Please try again or contact support directly."
                )
            
            keyboard = [
                [InlineKeyboardButton("📝 New Request", callback_data="support")],
                [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_support_submit: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            data = query.data
            
            # Handle different callback types
            if data == 'show_help':
                await self.handle_help(update, context)
            elif data == 'build':
                await self.handle_build(update, context)
            elif data == 'train':
                await self.handle_train(update, context)
            elif data == 'quest':
                await self.handle_quest(update, context)
            elif data == 'market':
                await self.handle_market(update, context)
            elif data.startswith('help_'):
                await self.handle_help_category(update, context)
            elif data.startswith('support_'):
                await self.handle_support_request(update, context)
            else:
                await query.answer("Invalid callback data")
                
        except Exception as e:
            logger.error(f"Error in handle_callback: {e}", exc_info=True)
            await self._handle_error(update, e)