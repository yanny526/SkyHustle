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
        """Handle the /start command"""
        try:
            player_id = str(update.effective_user.id)
            
            # Create player if new
            if not self.player_manager.get_player(player_id):
                result = self.player_manager.create_player(player_id)
                if not result['success']:
                    await update.message.reply_text("❌ Error creating player profile!")
                    return
                
                # Start tutorial for new player
                tutorial_result = self.tutorial_manager.start_tutorial(player_id)
                if tutorial_result['success']:
                    # Grant starter bonus
                    self.resource_manager.add_resources(self.tutorial_manager.starter_bonuses['resources'])
                    
                    # Build starter buildings
                    for building_id, level in self.tutorial_manager.starter_bonuses['buildings'].items():
                        self.building_manager.build_building(player_id, building_id, level)
                    
                    # Train starter units
                    for unit_id, count in self.tutorial_manager.starter_bonuses['units'].items():
                        self.unit_manager.train_units(player_id, unit_id, count)
            
            # Update last login
            self.player_manager.update_last_login(player_id)
            
            # Get current tutorial step if in tutorial
            current_step = self.tutorial_manager.get_current_step(player_id)
            
            # Send welcome message
            message = (
                "🎮 Welcome to SkyHustle 2!\n\n"
                "Your adventure begins now. Use /help to see available commands."
            )
            
            if current_step:
                message += f"\n\n📚 Tutorial Step {current_step['step']}: {current_step['description']}"
            
            await update.message.reply_text(message)
            
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
            
            # Update resources
            self.resource_manager.update_resources()
            
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
            active_wars = self.alliance_war_manager.get_active_wars()
            
            for war in active_wars:
                if current_time >= war['end_time']:
                    self.alliance_war_manager.end_war(war['id'])
                    
        except Exception as e:
            logger.error(f"Error in _update_alliance_wars: {e}", exc_info=True)

    def get_daily_attack_suggestions(self, player_id: str) -> list:
        """Suggest 5 players to attack daily"""
        try:
            # Get all player IDs
            all_players = [p['player_id'] for p in self.player_manager.get_all_players()]
            # Exclude self
            all_players = [pid for pid in all_players if pid != player_id]
            # Exclude same alliance members
            player_alliance = self.alliance_manager.members.get(player_id)
            if player_alliance:
                same_alliance = set(self.alliance_manager.alliances[player_alliance]['members'])
                all_players = [pid for pid in all_players if pid not in same_alliance]
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