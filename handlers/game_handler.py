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
        """Show help message with available commands."""
        try:
            message = (
                "*SkyHustle 2 Commands*\n\n"
                "*Basic Commands:*\n"
                "`/start` \\- Start the game\n"
                "`/help` \\- Show this help message\n"
                "`/status` \\- Check your base status\n"
                "`/profile` \\- View your profile\n"
                "`/name <name>` \\- Set your player name\n"
                "`/achievements` \\- View your achievements\n"
                "`/leaderboard` \\- View the top players\n"
                "`/tutorial` \\- View your tutorial progress\n"
                "\n*Gameplay:*\n"
                "`/build` \\- Manage buildings\n"
                "`/train` \\- Train military units\n"
                "`/research` \\- Research technologies\n"
                "`/attack` \\- Attack other players\n"
                "`/quest` \\- Complete quests\n"
                "`/market` \\- Trade resources\n"
                "\n*Alliance:*\n"
                "`/create\\_alliance` \\- Create an alliance\n"
                "`/join\\_alliance` \\- Join an alliance\n"
                "`/alliance\\_chat` \\- Alliance chat\n"
                "`/alliance\\_donate` \\- Donate to your alliance\n"
                "`/alliance\\_war` \\- Declare alliance war\n"
                "`/alliance\\_manage` \\- Manage your alliance\n"
                "`/alliance\\_list` \\- List alliances\n"
                "`/alliance\\_info` \\- Alliance info\n"
                "`/alliance\\_promote` \\- Promote a member\n"
                "`/alliance\\_demote` \\- Demote a member\n"
                "`/alliance\\_transfer` \\- Transfer leadership\n"
                "`/alliance\\_requests` \\- View join requests\n"
                "`/alliance\\_war\\_rankings` \\- War rankings\n"
                "`/alliance\\_benefits` \\- Alliance benefits\n"
                "`/alliance\\_perks` \\- Alliance perks\n"
                "`/alliance\\_resources` \\- Alliance resources\n"
                "`/alliance\\_research` \\- Alliance research\n"
                "`/alliance\\_diplomacy` \\- Alliance diplomacy"
            )
            await update.message.reply_text(message, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error in handle_help: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_status(self, update, context):
        """Show player status: resources, buildings, etc."""
        try:
            player_id = str(update.effective_user.id)
            player = self.player_manager.get_player(player_id)
            if not player:
                await update.message.reply_text("❌ Player not found. Use /start to begin.")
                return
            
            # Ensure resources is a dictionary
            resources = player.get('resources', {})
            if not isinstance(resources, dict):
                resources = {}
            
            buildings = player.get('buildings', {})
            army = player.get('army', {})
            hustlecoins = player.get('hustlecoins', 0)
            level = player.get('level', 1)
            xp = player.get('xp', 0)
            
            message = (
                f"*Base Status*\n\n"
                f"Level: {level} | XP: {xp}\n"
                f"HustleCoins: {hustlecoins}\n\n"
                f"*Resources:*\n" + "\n".join(f"{k}: {v}" for k, v in resources.items()) + "\n\n"
                f"*Buildings:*\n" + ("\n".join(f"{k}: Level {v}" for k, v in buildings.items()) if buildings else "None") + "\n\n"
                f"*Army:*\n" + ("\n".join(f"{k}: {v}" for k, v in army.items()) if army else "None")
            )
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_status: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_achievements(self, update, context):
        """Show player's achievements."""
        try:
            player_id = str(update.effective_user.id)
            result = self.achievement_manager.get_player_achievements(player_id)
            if not result['success']:
                await update.message.reply_text("❌ Could not fetch achievements.")
                return
            achievements = result['achievements']
            if not achievements:
                await update.message.reply_text("No achievements yet. Start playing to earn some!")
                return
            message = "*Your Achievements:*\n\n"
            for ach in achievements:
                status = "✅" if ach['completed'] else "❌"
                message += f"{status} {ach['emoji']} {ach['name']}: {ach['description']}\n"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_achievements: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_profile(self, update, context):
        """Show player profile."""
        try:
            player_id = str(update.effective_user.id)
            player = self.player_manager.get_player(player_id)
            if not player:
                await update.message.reply_text("❌ Player not found. Use /start to begin.")
                return
            name = player.get('name', 'Unknown')
            level = player.get('level', 1)
            xp = player.get('xp', 0)
            created = player.get('created_at', 0)
            last_login = player.get('last_active', 0)
            message = (
                f"*Player Profile*\n\n"
                f"Name: {name}\n"
                f"Level: {level}\n"
                f"XP: {xp}\n"
                f"Created: {time.strftime('%Y-%m-%d', time.localtime(created)) if created else 'N/A'}\n"
                f"Last Login: {time.strftime('%Y-%m-%d %H:%M', time.localtime(last_login)) if last_login else 'N/A'}"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
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
        """Show top players by level and XP."""
        try:
            all_players = self.player_manager.get_all_players()
            if not all_players:
                await update.message.reply_text("No players found.")
                return
            # Sort by level, then XP
            sorted_players = sorted(all_players, key=lambda p: (-p.get('level', 1), -p.get('xp', 0)))
            message = "*Leaderboard*\n\n"
            for i, p in enumerate(sorted_players[:10], 1):
                name = p.get('name', 'Unknown')
                level = p.get('level', 1)
                xp = p.get('xp', 0)
                message += f"{i}. {name} - Level {level} ({xp} XP)\n"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_leaderboard: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_tutorial(self, update, context):
        """Show current tutorial step or guide."""
        try:
            player_id = str(update.effective_user.id)
            step = self.tutorial_manager.get_current_step(player_id)
            if not step:
                await update.message.reply_text("You have completed the tutorial or it hasn't started yet.")
                return
            message = f"*Tutorial Step {step['step']}*\n{step['description']}"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_tutorial: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_build(self, update, context):
        """Show and manage player buildings."""
        try:
            player_id = str(update.effective_user.id)
            buildings = self.building_manager.get_all_buildings(player_id)
            if not buildings:
                await update.message.reply_text("You have no buildings yet. Use /build to construct your first building!")
                return
            message = "*Your Buildings:*\n\n"
            for b_id, b in buildings.items():
                info = b.get('info', {})
                name = info.get('name', b_id)
                level = b.get('level', 1)
                max_level = info.get('max_level', '?')
                emoji = info.get('emoji', '')
                message += f"{emoji} {name}: Level {level}/{max_level}\n"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_build: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_train(self, update, context):
        """Show and manage army training."""
        try:
            player_id = str(update.effective_user.id)
            units = self.unit_manager.get_all_units(player_id)
            if not units:
                await update.message.reply_text("You have no units yet. Use /train to train your first army!")
                return
            message = "*Your Army:*\n\n"
            for u_id, u in units.items():
                name = u.get('name', u_id)
                count = u.get('count', 0)
                emoji = u.get('emoji', '')
                message += f"{emoji} {name}: {count}\n"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_train: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_research(self, update, context):
        """Show and manage research."""
        try:
            player_id = str(update.effective_user.id)
            researches = self.research_manager.get_all_research(player_id)
            if not researches:
                await update.message.reply_text("No research started yet. Use /research to begin!")
                return
            message = "*Your Research:*\n\n"
            for r_id, r in researches.items():
                name = r.get('name', r_id)
                level = r.get('level', 0)
                emoji = r.get('emoji', '')
                message += f"{emoji} {name}: Level {level}\n"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_research: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_attack(self, update, context):
        """Initiate an attack on another player."""
        try:
            player_id = str(update.effective_user.id)
            suggestions = self.get_daily_attack_suggestions(player_id)
            if not suggestions:
                await update.message.reply_text("No valid targets found for attack.")
                return
            message = "*Suggested Targets to Attack:*\n\n"
            for s in suggestions:
                message += f"{s['name']} (Level {s['level']})\n"
            message += "\nUse /attack <player_id> to attack a specific player."
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_attack: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_quest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quest command"""
        try:
            player_id = str(update.effective_user.id)
            quest_result = self.quest_manager.get_player_quests(player_id)
            
            if not quest_result.get('success'):
                await update.message.reply_text("You don't have any quests yet. Check back later!")
                return
                
            active_quests = quest_result.get('active_quests', [])
            completed_quests = quest_result.get('completed_quests', [])
            
            if not active_quests and not completed_quests:
                await update.message.reply_text("You don't have any quests yet. Check back later!")
                return
                
            message = "🎯 *Your Quests*\n\n"
            
            if active_quests:
                message += "*Active Quests:*\n"
                for quest in active_quests:
                    progress = (quest['progress'] / quest['target']) * 100
                    message += f"• {quest['name']}\n"
                    message += f"  {quest['description']}\n"
                    message += f"  Progress: {quest['progress']}/{quest['target']} ({progress:.1f}%)\n"
                    message += f"  Reward: {', '.join(f'{k}: {v}' for k, v in quest['reward'].items())}\n\n"
            
            if completed_quests:
                message += "\n*Completed Quests:*\n"
                for quest in completed_quests[-5:]:  # Show last 5 completed quests
                    message += f"• {quest['name']}\n"
                    message += f"  Reward: {', '.join(f'{k}: {v}' for k, v in quest['reward'].items())}\n\n"
            
            await update.message.reply_text(message, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"Error in handle_quest: {e}", exc_info=True)
            await update.message.reply_text("Sorry, there was an error processing your quests. Please try again later.")

    async def handle_market(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle market command"""
        try:
            player_id = str(update.effective_user.id)
            market_result = self.market_manager.get_market_listings()
            
            if not market_result.get('success'):
                await update.message.reply_text("The market is currently unavailable. Please try again later!")
                return
                
            listings = market_result.get('listings', [])
            
            if not listings:
                await update.message.reply_text("There are no active listings in the market right now.")
                return
                
            message = "🏪 *Market Listings*\n\n"
            
            for listing in listings:
                seller_name = self.player_manager.get_player_name(listing['seller_id'])
                message += f"*Listing ID:* `{listing['id']}`\n"
                message += f"*Seller:* {seller_name}\n"
                message += f"*Resources:* {', '.join(f'{k}: {v}' for k, v in listing['resources'].items())}\n"
                message += f"*Price:* {', '.join(f'{k}: {v}' for k, v in listing['price'].items())}\n"
                message += f"*Expires:* {time.strftime('%Y-%m-%d %H:%M', time.localtime(listing['expires_at']))}\n\n"
            
            message += "\nTo buy a listing, use /buy <listing_id>"
            
            await update.message.reply_text(message, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"Error in handle_market: {e}", exc_info=True)
            await update.message.reply_text("Sorry, there was an error accessing the market. Please try again later.")

    async def handle_callback(self, update, context):
        await update.callback_query.answer("Callback: (This is a placeholder. Implement your callback logic here.)")

    async def handle_friends(self, update, context):
        """Show and manage friends."""
        try:
            player_id = str(update.effective_user.id)
            friends = self.social_manager.get_friend_list(player_id)
            if not friends:
                await update.message.reply_text("You have no friends yet. Use /add_friend <player_id> to add one!")
                return
            message = "*Your Friends:*\n\n"
            for f in friends:
                name = f.get('player_id', 'Unknown')
                online = "🟢" if f.get('online') else "⚪"
                last_seen = f.get('last_seen', 0)
                last_seen_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(last_seen)) if last_seen else 'N/A'
                message += f"{online} {name} (Last seen: {last_seen_str})\n"
            await update.message.reply_text(message, parse_mode='Markdown')
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
            if not skills:
                await update.message.reply_text("No skills found. Unlock skills as you progress!")
                return
            message = "*Your Skills:*\n\n"
            for skill, value in skills.items():
                message += f"{skill}: {value}\n"
            await update.message.reply_text(message, parse_mode='Markdown')
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

    async def handle_create_alliance(self, update, context):
        """Create a new alliance."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args or len(context.args) < 2:
                await update.message.reply_text("Usage: /create_alliance <name> <description>")
                return
            name = context.args[0]
            description = " ".join(context.args[1:])
            result = self.alliance_manager.create_alliance(player_id, name, description)
            if result.get('success'):
                await update.message.reply_text(f"✅ Alliance '{name}' created!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not create alliance.')}")
        except Exception as e:
            logger.error(f"Error in handle_create_alliance: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_join_alliance(self, update, context):
        """Join an alliance."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /join_alliance <alliance_id>")
                return
            alliance_id = context.args[0]
            result = self.alliance_manager.join_alliance(player_id, alliance_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Joined alliance {alliance_id}!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not join alliance.')}")
        except Exception as e:
            logger.error(f"Error in handle_join_alliance: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_chat(self, update, context):
        """Show alliance chat."""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_player_alliance(player_id)
            if not alliance:
                await update.message.reply_text("You are not in an alliance.")
                return
            chat = self.alliance_manager.get_chat_history(alliance['alliance_id'])
            if not chat:
                await update.message.reply_text("No messages in alliance chat yet.")
                return
            message = "*Alliance Chat:*\n" + "\n".join(f"{msg['player_id']}: {msg['message']}" for msg in chat)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_chat: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_donate(self, update, context):
        """Donate resources to alliance."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args or len(context.args) < 2:
                await update.message.reply_text("Usage: /alliance_donate <alliance_id> <resource>:<amount> ...")
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
                await update.message.reply_text(f"✅ Donated to alliance {alliance_id}!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not donate resources.')}")
        except Exception as e:
            logger.error(f"Error in handle_alliance_donate: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_war(self, update, context):
        """Declare war on another alliance."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_war <target_alliance_id>")
                return
            target_alliance_id = context.args[0]
            result = self.alliance_manager.declare_war(player_id, target_alliance_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ War declared on alliance {target_alliance_id}!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not declare war.')}")
        except Exception as e:
            logger.error(f"Error in handle_alliance_war: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_manage(self, update, context):
        """Show alliance management options."""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_player_alliance(player_id)
            if not alliance:
                await update.message.reply_text("You are not in an alliance.")
                return
            message = f"*Alliance Management for {alliance['name']}*\n\n(Management features coming soon!)"
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_manage: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_list(self, update, context):
        """List all alliances."""
        try:
            alliances = self.alliance_manager.get_all_alliances()
            if not alliances:
                await update.message.reply_text("No alliances found.")
                return
            message = "*Alliances:*\n" + "\n".join(f"{a['name']} (ID: {a['alliance_id']})" for a in alliances)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_list: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_info(self, update, context):
        """Show info about an alliance."""
        try:
            if not context.args:
                await update.message.reply_text("Usage: /alliance_info <alliance_id>")
                return
            alliance_id = context.args[0]
            alliance = self.alliance_manager.get_alliance(alliance_id)
            if not alliance:
                await update.message.reply_text("Alliance not found.")
                return
            message = (
                f"*Alliance Info:*\n"
                f"Name: {alliance['name']}\n"
                f"Level: {alliance.get('level', 1)}\n"
                f"Leader: {alliance.get('leader', 'Unknown')}\n"
                f"Members: {alliance.get('members', [])}\n"
                f"Description: {alliance.get('description', '')}"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_info: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_promote(self, update, context):
        """Promote a member in the alliance."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_promote <member_id>")
                return
            member_id = context.args[0]
            result = self.alliance_manager.promote_member(player_id, member_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Promoted member {member_id}!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not promote member.')}")
        except Exception as e:
            logger.error(f"Error in handle_alliance_promote: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_demote(self, update, context):
        """Demote a member in the alliance."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_demote <member_id>")
                return
            member_id = context.args[0]
            result = self.alliance_manager.demote_member(player_id, member_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Demoted member {member_id}!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not demote member.')}")
        except Exception as e:
            logger.error(f"Error in handle_alliance_demote: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_transfer(self, update, context):
        """Transfer alliance leadership."""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await update.message.reply_text("Usage: /alliance_transfer <new_leader_id>")
                return
            new_leader_id = context.args[0]
            result = self.alliance_manager.transfer_leadership(player_id, new_leader_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ Leadership transferred to {new_leader_id}!")
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Could not transfer leadership.')}")
        except Exception as e:
            logger.error(f"Error in handle_alliance_transfer: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_requests(self, update, context):
        """Show join requests for the alliance."""
        try:
            player_id = str(update.effective_user.id)
            requests = self.alliance_manager.get_join_requests(player_id)
            if not requests:
                await update.message.reply_text("No join requests found.")
                return
            message = "*Join Requests:*\n" + "\n".join(f"{r['player_id']}" for r in requests)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_requests: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_war_rankings(self, update, context):
        """Show alliance war rankings."""
        try:
            rankings = self.alliance_manager.get_alliance_rankings()
            if not rankings:
                await update.message.reply_text("No alliance war rankings found.")
                return
            message = "*Alliance War Rankings:*\n" + "\n".join(f"{i+1}. {r['name']} (Level {r.get('level', 1)})" for i, r in enumerate(rankings))
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_war_rankings: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_benefits(self, update, context):
        """Show alliance benefits."""
        try:
            player_id = str(update.effective_user.id)
            benefits = self.alliance_manager.get_alliance_benefits(player_id)
            if not benefits:
                await update.message.reply_text("No alliance benefits found.")
                return
            message = "*Alliance Benefits:*\n" + "\n".join(f"{b['name']}: {b['description']}" for b in benefits)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_benefits: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_perks(self, update, context):
        """Show alliance perks."""
        try:
            player_id = str(update.effective_user.id)
            perks = self.alliance_manager.get_alliance_perks(player_id)
            if not perks:
                await update.message.reply_text("No alliance perks found.")
                return
            message = "*Alliance Perks:*\n" + "\n".join(f"{p['name']}: {p['description']}" for p in perks)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_perks: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_resources(self, update, context):
        """Show alliance resources."""
        try:
            player_id = str(update.effective_user.id)
            resources = self.alliance_manager.get_alliance_resources(player_id)
            if not resources:
                await update.message.reply_text("No alliance resources found.")
                return
            message = "*Alliance Resources:*\n" + "\n".join(f"{k}: {v}" for k, v in resources.items())
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_resources: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_research(self, update, context):
        """Show alliance research."""
        try:
            player_id = str(update.effective_user.id)
            research = self.alliance_manager.get_alliance_research(player_id)
            if not research:
                await update.message.reply_text("No alliance research found.")
                return
            message = "*Alliance Research:*\n" + "\n".join(f"{r['name']}: Level {r['level']}" for r in research)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_research: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_alliance_diplomacy(self, update, context):
        """Show alliance diplomacy status."""
        try:
            player_id = str(update.effective_user.id)
            diplomacy = self.alliance_manager.get_alliance_diplomacy(player_id)
            if not diplomacy:
                await update.message.reply_text("No alliance diplomacy data found.")
                return
            message = "*Alliance Diplomacy:*\n" + "\n".join(f"{d['target']}: {d['status']} ({d['points']} pts)" for d in diplomacy)
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_alliance_diplomacy: {e}", exc_info=True)
            await self._handle_error(update, e)