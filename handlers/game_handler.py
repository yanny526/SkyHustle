"""
Main game handler for SkyHustle 2
Manages the Telegram bot interface and game state
"""

import time
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.resource_manager import ResourceManager
from modules.building_manager import BuildingManager
from modules.unit_manager import UnitManager
from modules.research_manager import ResearchManager
from modules.combat_manager import CombatManager
from modules.alliance_manager import AllianceManager
from modules.alliance_war_manager import AllianceWarManager
from modules.quest_manager import QuestManager
from modules.market_manager import MarketManager
from modules.achievement_manager import AchievementManager
from modules.daily_rewards_manager import DailyRewardsManager
from modules.player_manager import PlayerManager
from modules.tutorial_manager import TutorialManager
from modules.social_manager import SocialManager
from modules.progression_manager import ProgressionManager
from modules.alliance_benefits_manager import AllianceBenefitsManager
from modules.alliance_resource_manager import AllianceResourceManager
from modules.alliance_research_manager import AllianceResearchManager
from modules.alliance_diplomacy_manager import AllianceDiplomacyManager
from config.game_config import RESOURCES, BUILDINGS, UNITS, RESEARCH, ACHIEVEMENTS, DAILY_REWARDS, EVENTS, COMBAT, ALLIANCE_SETTINGS, QUEST_TYPES, MARKET_SETTINGS, MARKET_EVENTS

class GameHandler:
    def __init__(self):
        self.resource_manager = ResourceManager()
        self.building_manager = BuildingManager()
        self.unit_manager = UnitManager()
        self.research_manager = ResearchManager()
        self.combat_manager = CombatManager()
        self.alliance_manager = AllianceManager()
        self.alliance_war_manager = AllianceWarManager()
        self.quest_manager = QuestManager()
        self.market_manager = MarketManager()
        self.achievement_manager = AchievementManager()
        self.daily_rewards_manager = DailyRewardsManager()
        self.player_manager = PlayerManager()
        self.tutorial_manager = TutorialManager()
        self.social_manager = SocialManager()
        self.progression_manager = ProgressionManager()
        self.alliance_benefits_manager = AllianceBenefitsManager()
        self.alliance_resource_manager = AllianceResourceManager()
        self.alliance_research_manager = AllianceResearchManager()
        self.alliance_diplomacy_manager = AllianceDiplomacyManager()
        self.last_update = time.time()
        self.active_events = {}
        self.achievements = set()
        self.last_battle_time = {}

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
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
        if current_step:
            welcome_message = current_step['message']
        else:
            welcome_message = (
                "🌍 *Welcome to SkyHustle 2!* 🌍\n\n"
                "Build your empire, gather resources, and become the strongest commander!\n\n"
                "🎮 *Quick Start Guide:*\n"
                "1. Use /name to set your display name\n"
                "2. Use /status to check your base\n"
                "3. Use /build to construct buildings\n"
                "4. Use /train to create units\n"
                "5. Use /research to unlock upgrades\n\n"
                "🎁 *Daily Rewards:*\n"
                "Login every day to claim special rewards!\n\n"
                "Use /help to see all available commands."
            )
        
        # Create welcome keyboard
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("🏗️ Build", callback_data="build")
            ],
            [
                InlineKeyboardButton("🎁 Daily Reward", callback_data="daily_reward"),
                InlineKeyboardButton("📜 Tutorial", callback_data="tutorial")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_tutorial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /tutorial command"""
        player_id = str(update.effective_user.id)
        
        # Get tutorial progress
        progress = self.tutorial_manager.get_tutorial_progress(player_id)
        
        if not progress['success']:
            # Start new tutorial
            result = self.tutorial_manager.start_tutorial(player_id)
            if not result['success']:
                await update.message.reply_text("❌ Error starting tutorial!")
                return
            
            current_step = self.tutorial_manager.get_current_step(player_id)
            message = current_step['message']
        else:
            # Show current tutorial step
            current_step = self.tutorial_manager.get_current_step(player_id)
            message = (
                f"📜 *Tutorial Progress: {progress['progress_percentage']:.0f}%*\n\n"
                f"{current_step['message']}\n\n"
                f"Completed: {progress['completed_steps']}/{progress['total_steps']} steps"
            )
        
        # Create keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /name command"""
        player_id = str(update.effective_user.id)
        
        # Check if name is provided
        if not context.args:
            await update.message.reply_text(
                "Please provide a name:\n"
                "/name <your_name>\n\n"
                "Rules:\n"
                "• 3-20 characters\n"
                "• Letters, numbers, and spaces only\n"
                "• Must be unique"
            )
            return
        
        # Get name from arguments
        name = " ".join(context.args)
        
        # Set player name
        result = self.player_manager.set_player_name(player_id, name)
        
        if result['success']:
            # Advance tutorial if in name step
            self.tutorial_manager.advance_tutorial(player_id, 'wait_for_name')
            
            await update.message.reply_text(
                f"✅ Your name has been set to: {name}"
            )
        else:
            await update.message.reply_text(f"❌ {result['message']}")

    async def handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /profile command"""
        player_id = str(update.effective_user.id)
        
        # Get player profile
        profile = self.player_manager.get_player_profile(player_id)
        
        if not profile['success']:
            await update.message.reply_text("❌ Error retrieving profile!")
            return
        
        # Format profile message
        message = (
            f"👤 *Player Profile*\n\n"
            f"Name: {profile['name']}\n"
            f"Level: {profile['level']} ⭐\n"
            f"Experience: {profile['experience']}/{profile['level'] * 1000} XP\n"
            f"Created: {time.strftime('%Y-%m-%d', time.localtime(profile['created_at']))}\n"
            f"Last Login: {time.strftime('%Y-%m-%d %H:%M', time.localtime(profile['last_login']))}"
        )
        
        # Create keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /leaderboard command"""
        # Get top players
        players = self.player_manager.get_leaderboard(10)
        
        if not players:
            await update.message.reply_text("❌ No players found!")
            return
        
        # Format leaderboard message
        message = "🏆 *Leaderboard*\n\n"
        
        for i, player in enumerate(players, 1):
            message += (
                f"{i}. {player['name']}\n"
                f"Level {player['level']} ⭐ | {player['experience']} XP\n\n"
            )
        
        # Create keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command"""
        player_id = str(update.effective_user.id)
        
        # Advance tutorial if in status step
        self.tutorial_manager.advance_tutorial(player_id, 'wait_for_status')
        
        # Update resources
        self.resource_manager.update_resources()
        
        # Get current resources
        resources = self.resource_manager.resources
        production_rates = self.resource_manager.get_production_rates()
        
        # Format resource status with progress bars
        resource_status = []
        for resource_id, resource in RESOURCES.items():
            amount = int(resources.get(resource_id, 0))
            rate = production_rates.get(resource_id, 0)
            # Create a simple progress bar
            progress = min(amount / 1000, 1.0)  # Assuming 1000 is max
            bar_length = 10
            filled = int(progress * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            resource_status.append(
                f"{resource['emoji']} {resource['name']}: {amount}\n"
                f"{bar} (+{rate:.1f}/min)"
            )
        
        # Get building status with progress indicators
        buildings = self.building_manager.get_all_buildings()
        building_status = []
        for building_id, building in buildings.items():
            level = building['level']
            info = building['info']
            max_level = info['max_level']
            progress = level / max_level
            bar_length = 5
            filled = int(progress * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            building_status.append(
                f"{info['emoji']} {info['name']} (Level {level}/{max_level})\n"
                f"{bar}"
            )
        
        # Create status message with sections
        status_message = (
            "📊 *Base Status*\n\n"
            "💎 *Resources:*\n" + "\n".join(resource_status) + "\n\n"
            "🏗️ *Buildings:*\n" + "\n".join(building_status) + "\n\n"
            "🎁 *Daily Streak:* " + "🔥" * self.daily_streak + f" ({self.daily_streak} days)\n"
            "⚡ *Active Events:* " + self._format_active_events()
        )
        
        # Add attack suggestions
        suggestions = self.get_daily_attack_suggestions(player_id)
        if suggestions:
            suggestion_lines = [f"• {s['name']} (Level {s['level']})" for s in suggestions]
            status_message += "\n\n🎯 *Suggested Targets to Attack Today:*\n" + "\n".join(suggestion_lines)
        
        # Create keyboard for quick actions
        keyboard = [
            [
                InlineKeyboardButton("🏗️ Build", callback_data="build"),
                InlineKeyboardButton("⚔️ Army", callback_data="army")
            ],
            [
                InlineKeyboardButton("🔬 Research", callback_data="research"),
                InlineKeyboardButton("📈 Leaderboard", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton("🎁 Daily Reward", callback_data="daily_reward"),
                InlineKeyboardButton("🏆 Achievements", callback_data="achievements")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    def _format_active_events(self) -> str:
        """Format active events for display"""
        if not self.active_events:
            return "None"
        
        events = []
        for event_id, event in self.active_events.items():
            time_left = int(event['end_time'] - time.time())
            if time_left > 0:
                minutes = time_left // 60
                seconds = time_left % 60
                events.append(f"{EVENTS[event_id]['emoji']} {minutes}m {seconds}s")
        return " | ".join(events)

    async def handle_daily_reward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle daily reward collection"""
        player_id = str(update.effective_user.id)
        
        # Check if player can claim reward
        check_result = self.daily_rewards_manager.can_claim_reward(player_id)
        if not check_result['success'] or not check_result['can_claim']:
            await update.message.reply_text(
                f"⏳ You've already claimed your daily reward.\n"
                f"Come back in {check_result['time_left']}!"
            )
            return
        
        # Claim reward
        result = self.daily_rewards_manager.claim_reward(player_id)
        if not result['success']:
            await update.message.reply_text("❌ Error claiming reward!")
            return
        
        # Add resources to player
        self.resource_manager.add_resources(result['reward'])
        
        # Format message
        message = (
            f"🎁 *Daily Reward Claimed!* 🎁\n\n"
            f"Day {result['streak']} of 7\n"
            f"Rewards:\n" + "\n".join(
                f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: +{amount}"
                for r, amount in result['reward'].items()
            )
        )
        
        if result['is_seventh_day']:
            message += "\n\n🎉 *7-Day Streak Bonus!* 🎉\nCome back tomorrow for even better rewards!"
        
        # Create keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_build(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /build command"""
        player_id = str(update.effective_user.id)
        
        # Advance tutorial if in build step
        self.tutorial_manager.advance_tutorial(player_id, 'wait_for_build')
        
        # Get current building levels
        buildings = self.building_manager.get_all_buildings()
        
        # Create keyboard with building options
        keyboard = []
        for building_id, building in buildings.items():
            level = building['level']
            info = building['info']
            max_level = info['max_level']
            
            # Calculate upgrade cost and time
            if level < max_level:
                cost = self.building_manager.get_upgrade_cost(building_id)
                time = self.building_manager.get_upgrade_time(building_id)
                
                # Format cost string
                cost_str = " | ".join(
                    f"{RESOURCES[r]['emoji']} {amount}"
                    for r, amount in cost.items()
                )
                
                # Create progress bar
                progress = level / max_level
                bar_length = 5
                filled = int(progress * bar_length)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                # Create button text with emoji and info
                button_text = (
                    f"{info['emoji']} {info['name']} {bar}\n"
                    f"Level {level}/{max_level} | {cost_str} | ⏱️ {time}s"
                )
            else:
                button_text = f"{info['emoji']} {info['name']} (MAX) ⭐"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"build_{building_id}")])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("⚔️ Army", callback_data="army")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create building menu message
        message = (
            "🏗️ *Building Menu*\n\n"
            "Upgrade your buildings to increase production and unlock new features!\n\n"
            "📈 *Current Production:*\n" + "\n".join(
                f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: +{rate:.1f}/min"
                for r, rate in self.resource_manager.get_production_rates().items()
            )
        )
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_army(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /army command"""
        player_id = str(update.effective_user.id)
        
        # Advance tutorial if in train step
        self.tutorial_manager.advance_tutorial(player_id, 'wait_for_train')
        
        # Get current army status
        units = self.unit_manager.get_all_units()
        
        # Create keyboard with unit options
        keyboard = []
        for unit_id, unit in units.items():
            info = unit['info']
            count = unit['count']
            
            # Calculate training cost and time
            cost = self.unit_manager.get_training_cost(unit_id)
            time = self.unit_manager.get_training_time(unit_id)
            
            # Format cost string
            cost_str = " | ".join(
                f"{RESOURCES[r]['emoji']} {amount}"
                for r, amount in cost.items()
            )
            
            # Create button text with emoji and info
            button_text = (
                f"{info['emoji']} {info['name']} ({count})\n"
                f"⚔️ {info['stats']['attack']} | 🛡️ {info['stats']['defense']} | ❤️ {info['stats']['hp']}\n"
                f"Train: {cost_str} | ⏱️ {time}s"
            )
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"train_{unit_id}")])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("🏗️ Build", callback_data="build")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create army menu message
        message = (
            "⚔️ *Army Management*\n\n"
            "Train units to defend your base and attack others!\n\n"
            "📊 *Current Army:*\n" + "\n".join(
                f"{unit['info']['emoji']} {unit['info']['name']}: {unit['count']}"
                for unit in units.values()
            ) + "\n\n"
            "🎯 *Training Queue:*\n" + self._format_training_queue()
        )
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    def _format_training_queue(self) -> str:
        """Format the current training queue"""
        queue = self.unit_manager.get_training_queue()
        if not queue:
            return "No units in training"
        
        queue_info = []
        for unit_id, count in queue.items():
            unit = self.unit_manager.get_unit_info(unit_id)
            queue_info.append(f"{unit['emoji']} {unit['name']}: {count}")
        
        return "\n".join(queue_info)

    async def _handle_unit_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE, unit_id: str):
        """Handle unit training request"""
        # Check if training is possible
        if self.unit_manager.can_train(unit_id):
            # Get training cost
            cost = self.unit_manager.get_training_cost(unit_id)
            
            # Check if player can afford it
            if self.resource_manager.can_afford(cost):
                # Spend resources and queue training
                self.resource_manager.spend_resources(cost)
                self.unit_manager.queue_training(unit_id)
                
                # Get unit info
                unit = self.unit_manager.get_unit_info(unit_id)
                training_time = self.unit_manager.get_training_time(unit_id)
                
                message = (
                    f"⚔️ *Training Started!*\n\n"
                    f"{unit['emoji']} {unit['name']} is being trained\n"
                    f"⏱️ Time remaining: {training_time} seconds\n\n"
                    f"Resources spent:\n" + "\n".join(
                        f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: -{amount}"
                        for r, amount in cost.items()
                    )
                )
            else:
                message = "❌ *Not enough resources!*\n\nCheck /status to see your current resources."
        else:
            message = "❌ *Cannot train!*\n\nCheck if you have enough population space."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Army", callback_data="army")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /research command"""
        player_id = str(update.effective_user.id)
        
        # Advance tutorial if in research step
        self.tutorial_manager.advance_tutorial(player_id, 'wait_for_research')
        
        # Get current research status
        research = self.research_manager.get_all_research()
        
        # Create keyboard with research options
        keyboard = []
        for category, items in research.items():
            # Add category header
            keyboard.append([InlineKeyboardButton(f"🔬 {category.title()}", callback_data=f"research_category_{category}")])
            
            # Add research items
            for research_id, item in items.items():
                info = item['info']
                level = item['level']
                max_level = info['max_level']
                
                # Calculate research cost and time
                if level < max_level:
                    cost = self.research_manager.get_research_cost(research_id)
                    time = self.research_manager.get_research_time(research_id)
                    
                    # Format cost string
                    cost_str = " | ".join(
                        f"{RESOURCES[r]['emoji']} {amount}"
                        for r, amount in cost.items()
                    )
                    
                    # Create progress bar
                    progress = level / max_level
                    bar_length = 5
                    filled = int(progress * bar_length)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    
                    # Create button text with emoji and info
                    button_text = (
                        f"{info['emoji']} {info['name']} {bar}\n"
                        f"Level {level}/{max_level} | {cost_str} | ⏱️ {time}s"
                    )
                else:
                    button_text = f"{info['emoji']} {info['name']} (MAX) ⭐"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"research_{research_id}")])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("🏗️ Build", callback_data="build")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create research menu message
        message = (
            "🔬 *Research Center*\n\n"
            "Research new technologies to improve your base!\n\n"
            "📈 *Current Bonuses:*\n" + self._format_research_bonuses() + "\n\n"
            "⏳ *Research Queue:*\n" + self._format_research_queue()
        )
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    def _format_research_bonuses(self) -> str:
        """Format current research bonuses"""
        bonuses = self.research_manager.get_all_bonuses()
        if not bonuses:
            return "No active bonuses"
        
        bonus_info = []
        for category, items in bonuses.items():
            for research_id, bonus in items.items():
                info = self.research_manager.get_research_info(research_id)
                bonus_info.append(
                    f"{info['emoji']} {info['name']}: +{bonus * 100:.0f}%"
                )
        
        return "\n".join(bonus_info)

    def _format_research_queue(self) -> str:
        """Format the current research queue"""
        queue = self.research_manager.get_research_queue()
        if not queue:
            return "No research in progress"
        
        queue_info = []
        for research_id, time_left in queue.items():
            info = self.research_manager.get_research_info(research_id)
            minutes = time_left // 60
            seconds = time_left % 60
            queue_info.append(f"{info['emoji']} {info['name']}: {minutes}m {seconds}s")
        
        return "\n".join(queue_info)

    async def _handle_research_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, research_id: str):
        """Handle research start request"""
        # Check if research is possible
        if self.research_manager.can_research(research_id):
            # Get research cost
            cost = self.research_manager.get_research_cost(research_id)
            
            # Check if player can afford it
            if self.resource_manager.can_afford(cost):
                # Spend resources and queue research
                self.resource_manager.spend_resources(cost)
                self.research_manager.queue_research(research_id)
                
                # Get research info
                research = self.research_manager.get_research_info(research_id)
                research_time = self.research_manager.get_research_time(research_id)
                
                message = (
                    f"🔬 *Research Started!*\n\n"
                    f"{research['emoji']} {research['name']} is being researched\n"
                    f"⏱️ Time remaining: {research_time} seconds\n\n"
                    f"Resources spent:\n" + "\n".join(
                        f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: -{amount}"
                        for r, amount in cost.items()
                    )
                )
            else:
                message = "❌ *Not enough resources!*\n\nCheck /status to see your current resources."
        else:
            message = "❌ *Cannot research!*\n\nThis technology has reached its maximum level."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Research", callback_data="research")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        message = (
            "🎮 *SkyHustle 2 Commands*\n\n"
            "📊 *Basic Commands:*\n"
            "/start - Start the game\n"
            "/help - Show this help message\n"
            "/status - Check your base status\n"
            "/build - Manage buildings\n"
            "/train - Train military units\n"
            "/research - Research technologies\n"
            "/army - View your army\n\n"
            "🎁 *Rewards & Progress:*\n"
            "/daily - Claim daily rewards\n"
            "/achievements - View achievements\n"
            "/events - Check active events\n\n"
            "⚔️ *Combat & Strategy:*\n"
            "/attack - Attack other players\n"
            "/defend - Set up defenses\n"
            "/spy - Scout other bases\n\n"
            "📈 *Economy & Resources:*\n"
            "/resources - View resource production\n"
            "/market - Trade resources\n"
            "/boost - Use resource boosters\n\n"
            "🎯 *Tips & Tricks:*\n"
            "• Check /status regularly to manage resources\n"
            "• Build production buildings early\n"
            "• Research technologies for bonuses\n"
            "• Train a balanced army\n"
            "• Complete daily tasks for rewards\n"
            "• Join events for special bonuses\n\n"
            "Need more help? Use /tutorial for a detailed guide!"
        )
        
        # Create keyboard with quick actions
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("🏗️ Build", callback_data="build")
            ],
            [
                InlineKeyboardButton("⚔️ Army", callback_data="army"),
                InlineKeyboardButton("🔬 Research", callback_data="research")
            ],
            [
                InlineKeyboardButton("🎁 Daily Reward", callback_data="daily_reward"),
                InlineKeyboardButton("📜 Tutorial", callback_data="tutorial")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /events command"""
        message = "🎉 *Active Events*\n\n"
        
        if not self.active_events:
            message += "No active events at the moment.\n\n"
            message += "Check back later for special events with great rewards!"
        else:
            for event_id, event in self.active_events.items():
                info = EVENTS[event_id]
                time_left = int(event['end_time'] - time.time())
                minutes = time_left // 60
                seconds = time_left % 60
                
                message += (
                    f"{info['emoji']} *{info['name']}*\n"
                    f"{info['description']}\n"
                    f"⏱️ Time remaining: {minutes}m {seconds}s\n\n"
                )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_attack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /attack command"""
        player_id = str(update.effective_user.id)
        
        # Advance tutorial if in attack step
        self.tutorial_manager.advance_tutorial(player_id, 'wait_for_attack')
        
        # Check battle cooldown
        if player_id in self.last_battle_time:
            time_since_last_battle = time.time() - self.last_battle_time[player_id]
            if time_since_last_battle < COMBAT['battle_cooldown']:
                cooldown_remaining = int(COMBAT['battle_cooldown'] - time_since_last_battle)
                await update.message.reply_text(
                    f"⏳ You must wait {cooldown_remaining} seconds before attacking again."
                )
                return
        
        # Get player's army
        army = self.unit_manager.get_all_units()
        if not any(unit['count'] > 0 for unit in army.values()):
            await update.message.reply_text(
                "❌ You need units to attack! Train some units first with /train"
            )
            return
        
        # Create attack keyboard with formations and tactics
        keyboard = []
        
        # Add formation selection
        keyboard.append([InlineKeyboardButton("🏰 Select Formation", callback_data="attack_formations")])
        
        # Add unit selection
        for unit_id, unit in army.items():
            if unit['count'] > 0:
                button_text = (
                    f"{unit['info']['emoji']} {unit['info']['name']} ({unit['count']})\n"
                    f"⚔️ {unit['info']['stats']['attack']} | 🛡️ {unit['info']['stats']['defense']}"
                )
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"attack_{unit_id}")])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data="army"),
            InlineKeyboardButton("📊 Status", callback_data="status")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "⚔️ *Attack Menu*\n\n"
            "1. Select your battle formation\n"
            "2. Choose your units\n"
            "3. Select your battle tactic\n\n"
            "📊 *Your Army:*\n" + "\n".join(
                f"{unit['info']['emoji']} {unit['info']['name']}: {unit['count']}"
                for unit in army.values()
                if unit['count'] > 0
            )
        )
        
        # Add attack suggestions
        suggestions = self.get_daily_attack_suggestions(player_id)
        if suggestions:
            suggestion_lines = [f"• {s['name']} (Level {s['level']})" for s in suggestions]
            message += "\n\n🎯 *Suggested Targets to Attack Today:*\n" + "\n".join(suggestion_lines)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_rankings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /rankings command"""
        player_id = str(update.effective_user.id)
        
        # Get player's ranking
        player_ranking = self.combat_manager.get_player_rankings(player_id)
        
        # Get league standings
        league = player_ranking['league']
        standings = self.combat_manager.get_league_standings(league)
        
        # Format standings
        standings_text = []
        for i, standing in enumerate(standings[:10], 1):  # Show top 10
            player_name = standing['player_id']  # In a real game, you'd look up the player's name
            standings_text.append(
                f"{i}. {player_name}: {standing['rating']} ⭐"
            )
        
        message = (
            f"🏆 *Rankings*\n\n"
            f"Your League: {league.title()}\n"
            f"Your Rating: {player_ranking['rating']} ⭐\n"
            f"Your Rank: #{player_ranking['rank']}\n\n"
            f"*{league.title()} League Standings:*\n" + "\n".join(standings_text)
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_battle_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /history command"""
        player_id = str(update.effective_user.id)
        
        # Get battle history
        history = self.combat_manager.get_battle_history(player_id)
        
        if not history:
            message = "📜 You haven't participated in any battles yet."
        else:
            # Format battle history
            history_text = []
            for battle in history:
                result = battle['result']
                if result['winner'] == 'attacker' and battle['attacker_id'] == player_id:
                    outcome = "✅ Victory"
                elif result['winner'] == 'defender' and battle['defender_id'] == player_id:
                    outcome = "✅ Victory"
                else:
                    outcome = "❌ Defeat"
                
                history_text.append(
                    f"{outcome}\n"
                    f"Rating Change: {result['rating_change']['attacker' if battle['attacker_id'] == player_id else 'defender']}\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M', time.localtime(battle['end_time']))}\n"
                )
            
            message = (
                "📜 *Battle History*\n\n" + "\n".join(history_text)
            )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def _handle_attack_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, unit_id: str):
        """Handle attack callback"""
        player_id = str(update.effective_user.id)
        
        # Get player's units
        units = self.unit_manager.get_all_units()
        if unit_id not in units or units[unit_id]['count'] == 0:
            await update.callback_query.answer("You don't have any of these units!")
            return
        
        # Find a random opponent
        # In a real game, you'd implement proper matchmaking
        opponent_id = "opponent_1"  # Placeholder
        
        # Initiate battle
        battle = self.combat_manager.initiate_battle(
            player_id,
            opponent_id,
            {unit_id: units[unit_id]['count']}
        )
        
        # Calculate battle result
        # In a real game, you'd get the opponent's units from their game state
        opponent_units = {unit_id: 5}  # Placeholder
        result = self.combat_manager.calculate_battle_result(battle['id'], opponent_units)
        
        # Update last battle time
        self.last_battle_time[player_id] = time.time()
        
        # Format battle result message
        if result['winner'] == 'attacker':
            message = (
                "⚔️ *Battle Result: Victory!* ⚔️\n\n"
                f"Rating Change: +{result['rating_change']['attacker']}\n\n"
                "Casualties:\n" + "\n".join(
                    f"{UNITS[unit_id]['emoji']} {UNITS[unit_id]['name']}: -{count}"
                    for unit_id, count in result['attacker_casualties'].items()
                )
            )
        else:
            message = (
                "⚔️ *Battle Result: Defeat* ⚔️\n\n"
                f"Rating Change: {result['rating_change']['attacker']}\n\n"
                "Casualties:\n" + "\n".join(
                    f"{UNITS[unit_id]['emoji']} {UNITS[unit_id]['name']}: -{count}"
                    for unit_id, count in result['attacker_casualties'].items()
                )
            )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Army", callback_data="army")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "tutorial":
            # Show tutorial
            await self.handle_tutorial(update, context)
            
        elif data == "status":
            # Update and show status
            self.resource_manager.update_resources()
            await self.handle_status(update, context)
            
        elif data == "build":
            # Show building menu
            await self.handle_build(update, context)
            
        elif data == "army":
            # Show army menu
            await self.handle_army(update, context)
            
        elif data == "research":
            # Show research menu
            await self.handle_research(update, context)
            
        elif data == "daily_reward":
            # Handle daily reward
            await self.handle_daily_reward(update, context)
            
        elif data == "achievements":
            # Show achievements
            await self.handle_achievements(update, context)
            
        elif data == "events":
            # Show events
            await self.handle_events(update, context)
            
        elif data == "rankings":
            # Show rankings
            await self.handle_rankings(update, context)
            
        elif data == "history":
            # Show battle history
            await self.handle_battle_history(update, context)
            
        elif data == "attack_formations":
            # Show formation selection
            await self._handle_attack_formations(update, context)
            
        elif data == "attack_tactics":
            # Show tactic selection
            await self._handle_attack_tactics(update, context)
            
        elif data.startswith("formation_"):
            # Handle formation selection
            formation_id = data.split("_")[1]
            context.user_data['selected_formation'] = formation_id
            await self._handle_attack_tactics(update, context)
            
        elif data.startswith("tactic_"):
            # Handle tactic selection
            tactic_id = data.split("_")[1]
            context.user_data['selected_tactic'] = tactic_id
            await self.handle_attack(update, context)
            
        elif data.startswith("build_"):
            # Handle building upgrade
            building_id = data.split("_")[1]
            await self._handle_building_upgrade(update, context, building_id)
            
        elif data.startswith("train_"):
            # Handle unit training
            unit_id = data.split("_")[1]
            await self._handle_unit_training(update, context, unit_id)
            
        elif data.startswith("research_"):
            # Handle research start
            research_id = data.split("_")[1]
            await self._handle_research_start(update, context, research_id)
            
        elif data.startswith("attack_"):
            # Handle attack
            unit_id = data.split("_")[1]
            await self._handle_attack_callback(update, context, unit_id)
            
        elif data == "tutorial":
            # Show tutorial
            await self._show_tutorial(update, context)
            
        elif data == "alliance":
            # Show alliance menu
            await self.handle_alliance(update, context)
            
        elif data == "alliance_create":
            # Show alliance creation form
            await update.callback_query.message.edit_text(
                "🏰 *Create Alliance*\n\n"
                "Please use the following format:\n"
                "/alliance_create <name> <description>"
            )
            
        elif data == "alliance_find":
            # Show alliance rankings
            rankings = self.alliance_manager.get_alliance_rankings()
            
            if not rankings:
                await update.callback_query.message.edit_text(
                    "❌ No alliances found!"
                )
                return
            
            # Format rankings
            rankings_text = "🏆 *Alliance Rankings*\n\n"
            for i, alliance in enumerate(rankings[:10], 1):
                rankings_text += (
                    f"{i}. {alliance['name']}\n"
                    f"Level: {alliance['level']} | Members: {alliance['member_count']}\n\n"
                )
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.edit_text(
                rankings_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif data == "alliance_chat":
            # Show alliance chat
            await self.handle_alliance_chat(update, context)
            
        elif data == "alliance_members":
            # Show alliance members
            alliance = self.alliance_manager.get_player_alliance(str(update.effective_user.id))
            if not alliance:
                return
            
            members_text = "👥 *Alliance Members*\n\n"
            
            # Leader
            members_text += f"👑 Leader: {alliance['leader_id']}\n\n"
            
            # Officers
            if alliance['officers']:
                members_text += "⚜️ Officers:\n"
                for officer in alliance['officers']:
                    members_text += f"• {officer}\n"
                members_text += "\n"
            
            # Members
            members_text += "👤 Members:\n"
            for member in alliance['members']:
                if member != alliance['leader_id'] and member not in alliance['officers']:
                    members_text += f"• {member}\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.edit_text(
                members_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif data == "alliance_war":
            # Show war declaration form
            await update.callback_query.message.edit_text(
                "⚔️ *Declare War*\n\n"
                "Please use the following format:\n"
                "/alliance_war <target_alliance_id>"
            )

        elif data == "quests":
            # Show quests menu
            await self.handle_quests(update, context)
            
        elif data == "refresh_quests":
            # Refresh quests
            player_id = str(update.effective_user.id)
            result = self.quest_manager.generate_quests(player_id)
            
            if result['success']:
                await self.handle_quests(update, context)
            else:
                await update.callback_query.message.edit_text(
                    f"❌ {result['message']}"
                )
            
        elif data == "quest_history":
            # Show quest history
            await self.handle_quest_history(update, context)

        elif data == "market":
            # Show market menu
            await self.handle_market(update, context)
            
        elif data == "market_create":
            # Show market creation form
            await update.callback_query.message.edit_text(
                "📝 *Create Market Listing*\n\n"
                "Please use the following format:\n"
                "/market_create <wood> <stone> <gold> <food> <price_wood> <price_stone> <price_gold> <price_food>"
            )
            
        elif data == "market_my_listings":
            # Show player's listings
            player_id = str(update.effective_user.id)
            result = self.market_manager.get_player_listings(player_id)
            
            if not result['success'] or not result['listings']:
                await update.callback_query.message.edit_text(
                    "❌ You have no active listings!"
                )
                return
            
            message = "📊 *My Listings*\n\n"
            
            for listing in result['listings']:
                # Format resources being sold
                resources_str = " | ".join(
                    f"{RESOURCES[r]['emoji']} {amount}"
                    for r, amount in listing['resources'].items()
                )
                
                # Format price
                price_str = " | ".join(
                    f"{RESOURCES[r]['emoji']} {amount}"
                    for r, amount in listing['price'].items()
                )
                
                message += (
                    f"ID: {listing['id']}\n"
                    f"Offering: {resources_str}\n"
                    f"Price: {price_str}\n"
                    f"Time left: {int((listing['expires_at'] - time.time()) / 60)}m\n\n"
                )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Market", callback_data="market")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.edit_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif data == "market_history":
            # Show trade history
            await self.handle_market_history(update, context)

        elif data.startswith("claim_"):
            # Handle achievement reward claim
            achievement_id = data.split("_")[1]
            await self.handle_achievement_claim(update, context)

        elif data == "friends":
            # Show friends menu
            await self.handle_friends(update, context)
            
        elif data == "add_friend":
            # Show add friend form
            await update.callback_query.message.edit_text(
                "➕ *Add Friend*\n\n"
                "Please use the following format:\n"
                "/add_friend <player_id>"
            )
            
        elif data == "chat":
            # Show chat menu
            await self.handle_chat(update, context)
            
        elif data.startswith("chat_"):
            # Show chat with specific friend
            target_id = data.split("_")[1]
            await self.handle_chat(update, context)
            
        elif data.startswith("accept_friend_"):
            # Accept friend request
            sender_id = data.split("_")[2]
            result = self.social_manager.accept_friend_request(
                str(update.effective_user.id),
                sender_id
            )
            
            if result['success']:
                await update.callback_query.message.edit_text(
                    f"✅ Friend request from {sender_id} accepted!"
                )
            else:
                await update.callback_query.message.edit_text(
                    f"❌ {result['message']}"
                )
            
        elif data.startswith("reject_friend_"):
            # Reject friend request
            sender_id = data.split("_")[2]
            # TODO: Implement reject friend request
            
        elif data.startswith("remove_friend_"):
            # Remove friend
            friend_id = data.split("_")[2]
            result = self.social_manager.remove_friend(
                str(update.effective_user.id),
                friend_id
            )
            
            if result['success']:
                await update.callback_query.message.edit_text(
                    f"✅ {friend_id} removed from friends."
                )
            else:
                await update.callback_query.message.edit_text(
                    f"❌ {result['message']}"
                )

        elif data == "level":
            # Show level info
            await self.handle_level(update, context)
            
        elif data == "skills":
            # Show skills menu
            await self.handle_skills(update, context)
            
        elif data.startswith("skill_tree_"):
            # Show specific skill tree
            tree_id = data.split("_")[2]
            await self._handle_skill_tree(update, context, tree_id)
            
        elif data.startswith("unlock_skill_"):
            # Unlock/upgrade skill
            parts = data.split("_")
            tree_id = parts[2]
            skill_id = parts[3]
            await self._handle_skill_unlock(update, context, tree_id, skill_id)

        elif query.data.startswith("benefits_"):
            action = query.data.split("_")[1]
            
            if action == "view":
                # Show detailed benefits information
                user_id = update.effective_user.id
                alliance_id = self.alliance_manager.get_player_alliance(user_id)
                alliance = self.alliance_manager.get_alliance(alliance_id)
                benefits = self.alliance_benefits_manager.get_member_benefits(user_id, alliance)
                
                message = (
                    f"📊 *Detailed Benefits*\n\n"
                    f"*Base Benefits (Level {alliance['level']}):*\n"
                    f"• Resource Bonus: +{benefits['resource_bonus']*100:.1f}%\n"
                    f"• XP Bonus: +{benefits['xp_bonus']*100:.1f}%\n"
                    f"• Production Bonus: +{benefits['production_bonus']*100:.1f}%\n"
                    f"• Research Bonus: +{benefits['research_bonus']*100:.1f}%\n"
                    f"• Combat Bonus: +{benefits['combat_bonus']*100:.1f}%\n"
                    f"• Defense Bonus: +{benefits['defense_bonus']*100:.1f}%\n\n"
                    f"*XP Milestone Bonuses:*\n"
                )
                
                for milestone in ALLIANCE_SETTINGS['xp_milestones']:
                    if alliance['xp'] >= milestone['xp']:
                        message += f"• {milestone['xp']:,} XP: +{milestone['bonus']*100:.1f}% bonus\n"
                        
                await query.edit_message_text(message, parse_mode='Markdown')
                
            elif action == "perks":
                await self.handle_alliance_perks(update, context)
                
            elif action == "unlock":
                await self.handle_alliance_perks(update, context)
                
            elif action == "manage":
                if not self.alliance_manager.is_alliance_leader(update.effective_user.id):
                    await query.edit_message_text("Only alliance leaders can manage benefits.")
                    return
                    
                # Show benefits management options
                keyboard = [
                    [InlineKeyboardButton("Add Temporary Bonus", callback_data="benefits_add_bonus")],
                    [InlineKeyboardButton("Remove Temporary Bonus", callback_data="benefits_remove_bonus")],
                    [InlineKeyboardButton("View Active Bonuses", callback_data="benefits_view_bonuses")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "Select a benefits management option:",
                    reply_markup=reply_markup
                )
                
        elif query.data.startswith("perk_unlock_"):
            perk_id = query.data.split("_")[2]
            user_id = update.effective_user.id
            
            if not self.alliance_manager.is_alliance_leader(user_id):
                await query.edit_message_text("Only alliance leaders can unlock perks.")
                return
                
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            alliance = self.alliance_manager.get_alliance(alliance_id)
            
            if self.alliance_benefits_manager.unlock_perk(alliance_id, perk_id):
                await query.edit_message_text(f"Successfully unlocked the {ALLIANCE_SETTINGS['perks'][perk_id]['name']} perk!")
            else:
                await query.edit_message_text("Failed to unlock perk. Make sure you have enough XP and the perk isn't already active.")
                
        elif query.data == "alliance_resources":
            await self.handle_alliance_resources(update, context)
            
        elif query.data == "alliance_withdraw":
            await self.handle_alliance_withdraw(update, context)
            
        elif query.data == "alliance_distribute":
            await self.handle_alliance_distribute(update, context)
            
        elif query.data == "alliance_protection":
            await self.handle_alliance_protection(update, context)
            
        elif query.data.startswith("withdraw_"):
            resource_id = query.data.split("_")[1]
            # Handle resource withdrawal
            # TODO: Implement withdrawal amount selection
            
        elif query.data.startswith("distribute_"):
            resource_id = query.data.split("_")[1]
            # Handle resource distribution
            # TODO: Implement distribution target and amount selection
            
        elif query.data == "protection_enable":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            # Check if alliance can afford protection
            cost = ALLIANCE_SETTINGS['resource_management']['protection']['cost']
            if not self.alliance_resource_manager.remove_resources(alliance_id, cost):
                await query.edit_message_text("❌ Not enough resources to enable protection!")
                return
                
            # Enable protection
            duration = ALLIANCE_SETTINGS['resource_management']['protection']['duration']
            if self.alliance_resource_manager.enable_resource_protection(alliance_id, duration):
                await query.edit_message_text("✅ Resource protection enabled!")
            else:
                await query.edit_message_text("❌ Failed to enable protection!")
                
        elif query.data == "protection_disable":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            if self.alliance_resource_manager.disable_resource_protection(alliance_id):
                await query.edit_message_text("✅ Resource protection disabled!")
            else:
                await query.edit_message_text("❌ Failed to disable protection!")

        elif query.data == "alliance_research":
            await self.handle_alliance_research(update, context)
            
        elif query.data == "alliance_research_available":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            available_research = self.alliance_research_manager.get_available_research(alliance_id)
            
            if not available_research:
                await query.edit_message_text(
                    "❌ No research projects available.\n"
                    "Complete current research to unlock more projects."
                )
                return
                
            # Group research by category
            research_by_category = {}
            for research in available_research:
                category = research['category']
                if category not in research_by_category:
                    research_by_category[category] = []
                research_by_category[category].append(research)
                
            # Create message
            message = "🔬 *Available Research*\n\n"
            
            for category, projects in research_by_category.items():
                category_info = ALLIANCE_SETTINGS['research']['categories'][category]
                message += f"{category_info['icon']} *{category_info['name']}*\n"
                message += f"{category_info['description']}\n\n"
                
                for project in projects:
                    message += (
                        f"*{project['name']}*\n"
                        f"{project['description']}\n"
                        f"Cost: {project['cost']:,} resources\n"
                        f"Benefits:\n"
                    )
                    
                    for benefit_type, value in project['benefits'].items():
                        benefit_name = ALLIANCE_SETTINGS['research']['benefits'][benefit_type]
                        message += f"• {benefit_name}: +{value * 100:.1f}%\n"
                        
                    message += "\n"
                    
            keyboard = []
            if self.alliance_manager.is_alliance_leader(user_id):
                for research in available_research:
                    keyboard.append([InlineKeyboardButton(
                        f"Start {research['name']}",
                        callback_data=f"research_start_{research['research_id']}"
                    )])
                    
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_research")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "alliance_research_history":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            history = self.alliance_research_manager.get_research_history(alliance_id)
            
            if not history:
                await query.edit_message_text(
                    "📜 No research history available."
                )
                return
                
            message = "📜 *Research History*\n\n"
            
            for research in history:
                research_info = ALLIANCE_SETTINGS['research']['projects'][research['research_id']]
                completion_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(research['completion_time']))
                
                message += (
                    f"*{research_info['name']}*\n"
                    f"Completed: {completion_time}\n"
                    f"Contributors: {len(research['contributions'])}\n\n"
                )
                
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance_research")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "alliance_research_current":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            active_research = self.alliance_research_manager.get_active_research(alliance_id)
            
            if not active_research:
                await query.edit_message_text(
                    "❌ No active research project."
                )
                return
                
            research_info = ALLIANCE_SETTINGS['research']['projects'][active_research['research_id']]
            progress = (active_research['total_contributions'] / active_research['required_contributions']) * 100
            bar_length = 10
            filled = int(progress / 10)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            message = (
                f"🔬 *Current Research*\n\n"
                f"*{research_info['name']}*\n"
                f"{research_info['description']}\n\n"
                f"Progress: {bar} ({progress:.1f}%)\n"
                f"Contributions: {active_research['total_contributions']:,}/{active_research['required_contributions']:,}\n\n"
                f"*Top Contributors:*\n"
            )
            
            # Sort contributors by contribution amount
            contributors = sorted(
                self.alliance_research_manager.contributions[alliance_id].items(),
                key=lambda x: x[1]['total_contributed'],
                reverse=True
            )[:5]  # Show top 5 contributors
            
            for player_id, contribution in contributors:
                message += f"• {player_id}: {contribution['total_contributed']:,}\n"
                
            keyboard = [
                [InlineKeyboardButton("Contribute Resources", callback_data="alliance_research_contribute")],
                [InlineKeyboardButton("🔙 Back", callback_data="alliance_research")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "alliance_research_cancel":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            if not self.alliance_manager.is_alliance_leader(user_id):
                await query.edit_message_text(
                    "❌ Only alliance leaders can cancel research projects."
                )
                return
                
            if self.alliance_research_manager.cancel_research(alliance_id):
                await query.edit_message_text(
                    "✅ Research project cancelled."
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to cancel research project."
                )
                
        elif query.data.startswith("research_start_"):
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            if not self.alliance_manager.is_alliance_leader(user_id):
                await query.edit_message_text(
                    "❌ Only alliance leaders can start research projects."
                )
                return
                
            research_id = query.data.split("_")[2]
            
            if self.alliance_research_manager.start_research(alliance_id, research_id):
                await query.edit_message_text(
                    "✅ Research project started!"
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to start research project."
                )
                
        elif query.data.startswith("research_contribute_"):
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            resource_id = query.data.split("_")[2]
            
            # Get player's resources
            resources = self.resource_manager.get_resources(user_id)
            amount = resources.get(resource_id, 0)
            
            if amount < ALLIANCE_SETTINGS['research']['min_contribution']:
                await query.edit_message_text(
                    f"❌ Not enough {RESOURCES[resource_id]['name']} to contribute."
                )
                return
                
            # Contribute resources
            contribution = {resource_id: amount}
            if self.alliance_research_manager.contribute_resources(alliance_id, user_id, contribution):
                # Remove resources from player
                self.resource_manager.remove_resources(user_id, contribution)
                await query.edit_message_text(
                    f"✅ Contributed {amount:,} {RESOURCES[resource_id]['name']} to research!"
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to contribute resources."
                )

        elif data == "alliance_diplomacy":
            await self.handle_alliance_diplomacy(update, context)
            
        elif data == "diplomacy_relationships":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            relationships = self.alliance_diplomacy_manager.get_all_relationships(alliance_id)
            
            message = "🤝 *Diplomatic Relationships*\n\n"
            
            for target_id, relationship in relationships.items():
                target_alliance = self.alliance_manager.get_alliance(target_id)
                if target_alliance:
                    message += (
                        f"*{target_alliance['name']}*\n"
                        f"Status: {relationship['status'].title()}\n"
                        f"Points: {relationship['points']}\n\n"
                    )
                    
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif data == "diplomacy_treaties":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            treaties = self.alliance_diplomacy_manager.get_all_treaties(alliance_id)
            
            message = "📜 *Active Treaties*\n\n"
            
            if not treaties:
                message += "No active treaties."
            else:
                for target_id, treaty in treaties.items():
                    target_alliance = self.alliance_manager.get_alliance(target_id)
                    if target_alliance:
                        treaty_info = ALLIANCE_SETTINGS['diplomacy']['treaty_types'][treaty['type']]
                        time_left = int(treaty['end_time'] - time.time())
                        days = time_left // (24 * 3600)
                        message += (
                            f"*{treaty_info['name']} with {target_alliance['name']}*\n"
                            f"Duration: {days} days remaining\n"
                            f"Description: {treaty_info['description']}\n\n"
                        )
                        
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif data == "diplomacy_peace":
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            peace_treaties = self.alliance_diplomacy_manager.get_all_peace_treaties(alliance_id)
            
            message = "🕊️ *Active Peace Treaties*\n\n"
            
            if not peace_treaties:
                message += "No active peace treaties."
            else:
                for target_id, treaty in peace_treaties.items():
                    target_alliance = self.alliance_manager.get_alliance(target_id)
                    if target_alliance:
                        time_left = int(treaty['end_time'] - time.time())
                        days = time_left // (24 * 3600)
                        message += (
                            f"*Peace with {target_alliance['name']}*\n"
                            f"Duration: {days} days remaining\n\n"
                        )
                        
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data.startswith("diplomacy_propose_"):
            treaty_id = data.split("_")[2]
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            # Get available alliances
            available_alliances = []
            for target_id in self.alliance_manager.get_all_alliances():
                if target_id != alliance_id and not self.alliance_diplomacy_manager.get_treaty(alliance_id, target_id):
                    target_alliance = self.alliance_manager.get_alliance(target_id)
                    if target_alliance:
                        available_alliances.append(target_alliance)
                        
            if not available_alliances:
                await query.edit_message_text(
                    "❌ No available alliances to propose a treaty to.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")]])
                )
                return
                
            # Create keyboard with available alliances
            keyboard = []
            for target_alliance in available_alliances:
                keyboard.append([InlineKeyboardButton(
                    target_alliance['name'],
                    callback_data=f"diplomacy_propose_target_{treaty_id}_{target_alliance['id']}"
                )])
                
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            treaty_info = ALLIANCE_SETTINGS['diplomacy']['treaty_types'][treaty_id]
            message = (
                f"🤝 *Propose {treaty_info['name']}*\n\n"
                f"Description: {treaty_info['description']}\n"
                f"Duration: {treaty_info['duration'] // (24 * 3600)} days\n\n"
                f"Select an alliance to propose the treaty to:"
            )
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif data.startswith("diplomacy_propose_target_"):
            parts = data.split("_")
            treaty_id = parts[3]
            target_id = parts[4]
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            treaty_info = ALLIANCE_SETTINGS['diplomacy']['treaty_types'][treaty_id]
            
            # Create treaty
            if self.alliance_diplomacy_manager.create_treaty(
                alliance_id,
                target_id,
                treaty_id,
                treaty_info['duration'],
                {'proposed_by': user_id}
            ):
                await query.edit_message_text(
                    f"✅ Successfully proposed {treaty_info['name']} to the alliance!"
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to propose treaty."
                )
                
        elif data.startswith("diplomacy_peace_duration_"):
            days = int(data.split("_")[3])
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            # Get available alliances
            available_alliances = []
            for target_id in self.alliance_manager.get_all_alliances():
                if target_id != alliance_id and not self.alliance_diplomacy_manager.get_peace_treaty(alliance_id, target_id):
                    target_alliance = self.alliance_manager.get_alliance(target_id)
                    if target_alliance:
                        available_alliances.append(target_alliance)
                        
            if not available_alliances:
                await query.edit_message_text(
                    "❌ No available alliances to propose peace to.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")]])
                )
                return
                
            # Create keyboard with available alliances
            keyboard = []
            for target_alliance in available_alliances:
                keyboard.append([InlineKeyboardButton(
                    target_alliance['name'],
                    callback_data=f"diplomacy_peace_target_{days}_{target_alliance['id']}"
                )])
                
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"🕊️ *Propose Peace Treaty*\n\n"
                f"Duration: {days} days\n\n"
                f"Select an alliance to propose peace to:"
            )
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif data.startswith("diplomacy_peace_target_"):
            parts = data.split("_")
            days = int(parts[3])
            target_id = parts[4]
            user_id = str(update.effective_user.id)
            alliance_id = self.alliance_manager.get_player_alliance(user_id)
            
            # Create peace treaty
            if self.alliance_diplomacy_manager.create_peace_treaty(
                alliance_id,
                target_id,
                days * 24 * 3600,
                {'proposed_by': user_id}
            ):
                await query.edit_message_text(
                    f"✅ Successfully proposed peace treaty for {days} days!"
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to propose peace treaty."
                )

    def apply_alliance_benefits(self, user_id: int, value: float, benefit_type: str) -> float:
        """Apply alliance benefits to a value"""
        if not self.alliance_manager.is_in_alliance(user_id):
            return value
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        alliance = self.alliance_manager.get_alliance(alliance_id)
        
        if not alliance:
            return value
            
        benefits = self.alliance_benefits_manager.get_member_benefits(user_id, alliance)
        bonus = benefits.get(f"{benefit_type}_bonus", 0)
        
        return value * (1 + bonus)
        
    def update(self):
        """Update game state"""
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
        
        # Update alliance benefits
        for alliance_id in self.alliance_manager.get_all_alliances():
            self.alliance_benefits_manager.calculate_alliance_benefits(alliance_id)

    async def handle_alliance_resources(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance resource management commands"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to use resource management commands.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        alliance = self.alliance_manager.get_alliance(alliance_id)
        
        if not alliance:
            await update.message.reply_text("Error: Alliance not found.")
            return
            
        # Get current resources
        resources = self.alliance_resource_manager.get_alliance_resources(alliance_id)
        protection_status = self.alliance_resource_manager.get_protection_status(alliance_id)
        
        # Create keyboard for resource management
        keyboard = [
            [InlineKeyboardButton("Withdraw Resources", callback_data="alliance_withdraw")],
            [InlineKeyboardButton("Distribute Resources", callback_data="alliance_distribute")],
            [InlineKeyboardButton("View History", callback_data="alliance_history")]
        ]
        
        if self.alliance_manager.is_alliance_leader(user_id):
            keyboard.append([InlineKeyboardButton("Manage Protection", callback_data="alliance_protection")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format resource status
        resource_status = []
        for resource_id, amount in resources.items():
            max_storage = ALLIANCE_SETTINGS['resource_management']['max_storage'][resource_id]
            percentage = (amount / max_storage) * 100
            bar_length = 10
            filled = int(percentage / 10)
            bar = '█' * filled + '░' * (bar_length - filled)
            resource_status.append(
                f"{RESOURCES[resource_id]['emoji']} {RESOURCES[resource_id]['name']}: {amount:,}/{max_storage:,}\n"
                f"{bar} ({percentage:.1f}%)"
            )
        
        # Create message
        message = (
            f"💰 *Alliance Resources*\n\n"
            f"*Current Resources:*\n" + "\n".join(resource_status) + "\n\n"
            f"*Protection Status:*\n"
        )
        
        if protection_status['is_protected']:
            hours = protection_status['time_left'] // 3600
            minutes = (protection_status['time_left'] % 3600) // 60
            message += f"🛡️ Protected ({hours}h {minutes}m remaining)"
        else:
            message += "⚠️ Not Protected"
            
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_withdraw(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance resource withdrawal"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to withdraw resources.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        alliance = self.alliance_manager.get_alliance(alliance_id)
        
        if not alliance:
            await update.message.reply_text("Error: Alliance not found.")
            return
            
        # Get withdrawal limits based on role
        role = 'leader' if self.alliance_manager.is_alliance_leader(user_id) else \
               'officer' if user_id in alliance['officers'] else 'member'
        limit_percentage = ALLIANCE_SETTINGS['resource_management']['withdrawal_limits'][role]
        
        # Get current resources
        resources = self.alliance_resource_manager.get_alliance_resources(alliance_id)
        
        # Calculate withdrawal limits
        limits = {
            resource: int(amount * limit_percentage)
            for resource, amount in resources.items()
        }
        
        # Create keyboard for withdrawal
        keyboard = []
        for resource_id, limit in limits.items():
            if limit > 0:
                keyboard.append([InlineKeyboardButton(
                    f"Withdraw {RESOURCES[resource_id]['emoji']} {RESOURCES[resource_id]['name']} (Max: {limit:,})",
                    callback_data=f"withdraw_{resource_id}"
                )])
                
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_resources")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"💰 *Resource Withdrawal*\n\n"
            f"*Withdrawal Limits:*\n" + "\n".join(
                f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: {l:,}"
                for r, l in limits.items()
            ) + "\n\n"
            f"Select a resource to withdraw:"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_distribute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance resource distribution"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to distribute resources.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        alliance = self.alliance_manager.get_alliance(alliance_id)
        
        if not alliance:
            await update.message.reply_text("Error: Alliance not found.")
            return
            
        # Get current resources
        resources = self.alliance_resource_manager.get_alliance_resources(alliance_id)
        
        # Create keyboard for distribution
        keyboard = []
        for resource_id, amount in resources.items():
            if amount > 0:
                keyboard.append([InlineKeyboardButton(
                    f"Distribute {RESOURCES[resource_id]['emoji']} {RESOURCES[resource_id]['name']} ({amount:,})",
                    callback_data=f"distribute_{resource_id}"
                )])
                
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_resources")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"💰 *Resource Distribution*\n\n"
            f"*Available Resources:*\n" + "\n".join(
                f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: {a:,}"
                for r, a in resources.items()
            ) + "\n\n"
            f"Select a resource to distribute:"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_protection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance resource protection"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_alliance_leader(user_id):
            await update.message.reply_text("Only alliance leaders can manage resource protection.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        protection_status = self.alliance_resource_manager.get_protection_status(alliance_id)
        
        # Create keyboard for protection management
        keyboard = []
        
        if not protection_status['is_protected']:
            # Show protection cost
            cost = ALLIANCE_SETTINGS['resource_management']['protection']['cost']
            cost_str = " | ".join(
                f"{RESOURCES[r]['emoji']} {amount:,}"
                for r, amount in cost.items()
            )
            
            keyboard.append([InlineKeyboardButton(
                f"Enable Protection ({cost_str})",
                callback_data="protection_enable"
            )])
        else:
            hours = protection_status['time_left'] // 3600
            minutes = (protection_status['time_left'] % 3600) // 60
            keyboard.append([InlineKeyboardButton(
                f"Disable Protection ({hours}h {minutes}m remaining)",
                callback_data="protection_disable"
            )])
            
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_resources")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"🛡️ *Resource Protection*\n\n"
            f"*Current Status:*\n"
        )
        
        if protection_status['is_protected']:
            hours = protection_status['time_left'] // 3600
            minutes = (protection_status['time_left'] % 3600) // 60
            message += f"🛡️ Protected ({hours}h {minutes}m remaining)"
        else:
            message += "⚠️ Not Protected\n\n"
            message += "*Protection Cost:*\n" + "\n".join(
                f"{RESOURCES[r]['emoji']} {RESOURCES[r]['name']}: {amount:,}"
                for r, amount in ALLIANCE_SETTINGS['resource_management']['protection']['cost'].items()
            )
            
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_alliance_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance research commands"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to use research commands.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        alliance = self.alliance_manager.get_alliance(alliance_id)
        
        if not alliance:
            await update.message.reply_text("Error: Alliance not found.")
            return
            
        # Get current research status
        active_research = self.alliance_research_manager.get_active_research(alliance_id)
        research_benefits = self.alliance_research_manager.get_research_benefits(alliance_id)
        
        # Create keyboard for research management
        keyboard = [
            [InlineKeyboardButton("View Available Research", callback_data="alliance_research_available")],
            [InlineKeyboardButton("View Research History", callback_data="alliance_research_history")]
        ]
        
        if active_research:
            keyboard.append([InlineKeyboardButton("View Current Research", callback_data="alliance_research_current")])
            if self.alliance_manager.is_alliance_leader(user_id):
                keyboard.append([InlineKeyboardButton("Cancel Research", callback_data="alliance_research_cancel")])
                
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format message
        message = "🔬 *Alliance Research*\n\n"
        
        if active_research:
            research_info = ALLIANCE_SETTINGS['research']['projects'][active_research['research_id']]
            progress = (active_research['total_contributions'] / active_research['required_contributions']) * 100
            bar_length = 10
            filled = int(progress / 10)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            message += (
                f"*Current Research:*\n"
                f"{research_info['name']}\n"
                f"{research_info['description']}\n"
                f"Progress: {bar} ({progress:.1f}%)\n"
                f"Contributions: {active_research['total_contributions']:,}/{active_research['required_contributions']:,}\n\n"
            )
        else:
            message += "No active research project.\n\n"
            
        if research_benefits:
            message += "*Active Benefits:*\n"
            for benefit_type, value in research_benefits.items():
                benefit_name = ALLIANCE_SETTINGS['research']['benefits'][benefit_type]
                message += f"• {benefit_name}: +{value * 100:.1f}%\n"
                
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_research_contribute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance research contributions"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to contribute to research.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        active_research = self.alliance_research_manager.get_active_research(alliance_id)
        
        if not active_research:
            await update.message.reply_text("No active research project to contribute to.")
            return
            
        # Get player's contributions
        contributions = self.alliance_research_manager.get_contributions(alliance_id, user_id)
        
        # Check contribution cooldown
        if time.time() - contributions['last_contribution'] < ALLIANCE_SETTINGS['research']['contribution_cooldown']:
            cooldown_remaining = int(ALLIANCE_SETTINGS['research']['contribution_cooldown'] - 
                                   (time.time() - contributions['last_contribution']))
            await update.message.reply_text(
                f"⏳ You must wait {cooldown_remaining} seconds before contributing again."
            )
            return
            
        # Check daily contribution limit
        if contributions['total_contributed'] >= ALLIANCE_SETTINGS['research']['max_contribution_per_day']:
            await update.message.reply_text(
                "❌ You have reached your daily contribution limit."
            )
            return
            
        # Get player's resources
        resources = self.resource_manager.get_resources(user_id)
        
        # Create keyboard for resource contribution
        keyboard = []
        for resource_id, amount in resources.items():
            if amount >= ALLIANCE_SETTINGS['research']['min_contribution']:
                keyboard.append([InlineKeyboardButton(
                    f"Contribute {RESOURCES[resource_id]['emoji']} {RESOURCES[resource_id]['name']} ({amount:,})",
                    callback_data=f"research_contribute_{resource_id}"
                )])
                
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_research")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"💰 *Research Contribution*\n\n"
            f"*Current Progress:*\n"
            f"Total: {active_research['total_contributions']:,}/{active_research['required_contributions']:,}\n"
            f"Your Contributions: {contributions['total_contributed']:,}\n"
            f"Daily Limit: {ALLIANCE_SETTINGS['research']['max_contribution_per_day']:,}\n\n"
            f"Select resources to contribute:"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_alliance_diplomacy(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance diplomacy commands"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to use diplomacy commands.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        alliance = self.alliance_manager.get_alliance(alliance_id)
        
        if not alliance:
            await update.message.reply_text("Error: Alliance not found.")
            return
            
        # Get current diplomatic status
        relationships = self.alliance_diplomacy_manager.get_all_relationships(alliance_id)
        treaties = self.alliance_diplomacy_manager.get_all_treaties(alliance_id)
        peace_treaties = self.alliance_diplomacy_manager.get_all_peace_treaties(alliance_id)
        
        # Create keyboard for diplomacy management
        keyboard = [
            [InlineKeyboardButton("View Relationships", callback_data="diplomacy_relationships")],
            [InlineKeyboardButton("View Treaties", callback_data="diplomacy_treaties")],
            [InlineKeyboardButton("View Peace Treaties", callback_data="diplomacy_peace")]
        ]
        
        if self.alliance_manager.is_alliance_leader(user_id):
            keyboard.extend([
                [InlineKeyboardButton("Propose Treaty", callback_data="diplomacy_propose")],
                [InlineKeyboardButton("Propose Peace", callback_data="diplomacy_peace_propose")]
            ])
            
        keyboard.append([InlineKeyboardButton("View History", callback_data="diplomacy_history")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format message
        message = "🤝 *Alliance Diplomacy*\n\n"
        
        # Add relationship summary
        message += "*Current Relationships:*\n"
        for target_id, relationship in relationships.items():
            target_alliance = self.alliance_manager.get_alliance(target_id)
            if target_alliance:
                message += f"• {target_alliance['name']}: {relationship['status'].title()} ({relationship['points']} points)\n"
                
        # Add active treaties
        if treaties:
            message += "\n*Active Treaties:*\n"
            for target_id, treaty in treaties.items():
                target_alliance = self.alliance_manager.get_alliance(target_id)
                if target_alliance:
                    treaty_info = ALLIANCE_SETTINGS['diplomacy']['treaty_types'][treaty['type']]
                    time_left = int(treaty['end_time'] - time.time())
                    days = time_left // (24 * 3600)
                    message += f"• {treaty_info['name']} with {target_alliance['name']} ({days} days left)\n"
                    
        # Add peace treaties
        if peace_treaties:
            message += "\n*Active Peace Treaties:*\n"
            for target_id, treaty in peace_treaties.items():
                target_alliance = self.alliance_manager.get_alliance(target_id)
                if target_alliance:
                    time_left = int(treaty['end_time'] - time.time())
                    days = time_left // (24 * 3600)
                    message += f"• Peace with {target_alliance['name']} ({days} days left)\n"
                    
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_diplomacy_propose(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance treaty proposal"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_alliance_leader(user_id):
            await update.message.reply_text("Only alliance leaders can propose treaties.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        
        # Create keyboard with treaty types
        keyboard = []
        for treaty_id, treaty in ALLIANCE_SETTINGS['diplomacy']['treaty_types'].items():
            keyboard.append([InlineKeyboardButton(
                f"{treaty['name']} ({treaty['duration'] // (24 * 3600)} days)",
                callback_data=f"diplomacy_propose_{treaty_id}"
            )])
            
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "🤝 *Propose Treaty*\n\n"
            "Select the type of treaty you want to propose:"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_diplomacy_peace(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance peace treaty proposal"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_alliance_leader(user_id):
            await update.message.reply_text("Only alliance leaders can propose peace treaties.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        
        # Create keyboard with duration options
        keyboard = []
        for days in [1, 3, 7, 14, 30]:
            keyboard.append([InlineKeyboardButton(
                f"{days} days",
                callback_data=f"diplomacy_peace_duration_{days}"
            )])
            
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "🕊️ *Propose Peace Treaty*\n\n"
            "Select the duration of the peace treaty:"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def handle_alliance_diplomacy_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle alliance diplomatic history"""
        user_id = str(update.effective_user.id)
        
        if not self.alliance_manager.is_in_alliance(user_id):
            await update.message.reply_text("You must be in an alliance to view diplomatic history.")
            return
            
        alliance_id = self.alliance_manager.get_player_alliance(user_id)
        
        # Get diplomatic actions
        actions = self.alliance_diplomacy_manager.get_diplomatic_actions(alliance_id)
        
        if not actions:
            await update.message.reply_text("No diplomatic actions recorded.")
            return
            
        # Format message
        message = "📜 *Diplomatic History*\n\n"
        
        for action in actions:
            target_alliance = self.alliance_manager.get_alliance(action['details']['target_alliance'])
            if target_alliance:
                action_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(action['timestamp']))
                message += (
                    f"*{action_time}*\n"
                    f"Action: {action['type'].replace('_', ' ').title()}\n"
                    f"Target: {target_alliance['name']}\n\n"
                )
                
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="alliance_diplomacy")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    def get_daily_attack_suggestions(self, player_id: str) -> list:
        """Suggest 5 players to attack daily (not self, not in same alliance, active recently)"""
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