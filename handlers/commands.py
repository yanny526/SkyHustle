"""
Command handlers for the SkyHustle Telegram bot
Handles all the commands that users can send to the bot
"""
import logging
import os
from datetime import datetime, timedelta
import asyncio
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from constants import BUILDINGS, UNITS, RESEARCH, MESSAGES, WEATHER_MESSAGES
from modules.player import (
    get_player, create_player, update_player, 
    claim_daily_reward, check_achievement_progress,
    format_status_message
)
from modules.buildings import (
    get_player_buildings, add_building_to_queue, 
    get_available_buildings, check_building_prerequisites
)
from modules.units import (
    get_player_units, add_unit_to_queue,
    get_available_units, check_unit_prerequisites
)
from modules.research import (
    get_player_research, add_research_to_queue,
    get_available_research, check_research_prerequisites
)
from modules.alliance import (
    get_player_alliance, create_alliance, join_alliance,
    leave_alliance, get_alliance_info
)
from modules.battles import (
    attack_player, scan_for_targets, start_war, join_war
)
from modules.sheets_service import save_data, load_data

from utils.formatting import format_time, format_resources
from utils.validation import validate_name, is_name_unique, validate_quantity
from utils.logger import get_logger

logger = get_logger(__name__)

# Helper function to check if player exists, create if not
async def ensure_player_exists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ensure a player record exists for the current user"""
    player_id = str(update.effective_user.id)
    player = await get_player(player_id)
    
    if not player:
        username = update.effective_user.username or update.effective_user.first_name
        player = await create_player(player_id, username)
        logger.info(f"Created new player: {player_id}, username: {username}")
    
    return player

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    player = await ensure_player_exists(update, context)
    
    # Check if this is a returning player or new player
    if player.get("tutorial_completed", False):
        # Returning player
        welcome_text = f"Welcome back to SkyHustle, Commander {player['display_name']}!\n\nUse /status to check your base or /help for available commands."
    else:
        # New player
        welcome_text = MESSAGES["welcome"] + "\n\nWould you like to start the tutorial?"
        
        # Create inline keyboard for tutorial choice
        keyboard = [
            [
                InlineKeyboardButton("Begin Tutorial", callback_data='{"cmd":"tutorial","action":"start"}'),
                InlineKeyboardButton("Skip Tutorial", callback_data='{"cmd":"tutorial","action":"skip"}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        return
    
    await update.message.reply_text(welcome_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command - shows player's current resources and status"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # Get necessary data for status
    buildings = await get_player_buildings(player_id)
    units = await get_player_units(player_id)
    research = await get_player_research(player_id)
    
    # Format the status message
    status_message = await format_status_message(player, buildings, units, research)
    
    await update.message.reply_text(
        status_message,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    # Check for tutorial progress
    if not player.get("tutorial_completed", False) and context.user_data.get("tutorial_step") == "welcome":
        # Update tutorial state to the next step
        context.user_data["tutorial_step"] = "status_check"
        await update.message.reply_text(
            "Great! This is your base status. Now let's build your first structure.\n\n"
            "Try the /build command to see what buildings are available."
        )

async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /build command - queue buildings for construction"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # If no arguments, show available buildings
    if not context.args:
        available_buildings = await get_available_buildings(player_id)
        
        if not available_buildings:
            await update.message.reply_text("❌ No buildings available to construct.")
            return
        
        # Create keyboard with available buildings
        keyboard = []
        row = []
        for i, building_id in enumerate(available_buildings):
            building = BUILDINGS[building_id]
            button = InlineKeyboardButton(
                building["name"], 
                callback_data=f'{{"cmd":"build","id":"{building_id}"}}'
            )
            row.append(button)
            
            # 2 buttons per row
            if (i + 1) % 2 == 0 or i == len(available_buildings) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        building_list = "\n".join([
            f"• {BUILDINGS[b_id]['name']} - " +
            f"Cost: {format_resources(BUILDINGS[b_id]['base_cost'])}, " +
            f"Time: {format_time(BUILDINGS[b_id]['build_time'])}"
            for b_id in available_buildings
        ])
        
        await update.message.reply_text(
            f"ℹ️ **Available Buildings:**\n{building_list}\n\nSelect a building to construct:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Check tutorial progress
        if not player.get("tutorial_completed", False) and context.user_data.get("tutorial_step") == "status_check":
            context.user_data["tutorial_step"] = "build_instruction"
            await update.message.reply_text(
                "Excellent! Let's build a Mineral Extractor to start gathering resources.\n\n"
                "Select Mineral Extractor from the menu or use /build mineral_extractor."
            )
        
        return
    
    # Process building request with arguments
    building_id = context.args[0].lower()
    quantity = 1
    
    # Check if quantity is specified
    if len(context.args) > 1:
        try:
            quantity = int(context.args[1])
            if not validate_quantity(quantity):
                await update.message.reply_text(MESSAGES["error_invalid_quantity"])
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid quantity. Must be a number.")
            return
    
    # Validate building type
    if building_id not in BUILDINGS:
        await update.message.reply_text(MESSAGES["error_invalid_building"])
        return
    
    # Check prerequisites
    if not await check_building_prerequisites(player_id, building_id):
        await update.message.reply_text(MESSAGES["error_prerequisites_not_met"])
        return
    
    # Try to add building to queue
    result = await add_building_to_queue(player_id, building_id, quantity)
    if not result["success"]:
        await update.message.reply_text(f"❌ {result['message']}")
        return
    
    # Success
    building_name = BUILDINGS[building_id]["name"]
    completion_time = format_time(result["build_time"])
    
    await update.message.reply_text(
        MESSAGES["success_build"].format(
            quantity=quantity,
            building_name=building_name,
            time=completion_time
        )
    )
    
    # Check tutorial progress
    if not player.get("tutorial_completed", False) and context.user_data.get("tutorial_step") == "build_instruction" and building_id == "mineral_extractor":
        context.user_data["tutorial_step"] = "first_build"
        await update.message.reply_text(
            "Your Mineral Extractor is under construction! Once completed, it will generate minerals automatically.\n\n"
            "Now let's train your first units. Try the /train command to see available units."
        )

async def train_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /train command - queue units for training"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # If no arguments, show available units
    if not context.args:
        available_units = await get_available_units(player_id)
        
        if not available_units:
            await update.message.reply_text("❌ No units available to train. Build required buildings first.")
            return
        
        # Create keyboard with available units
        keyboard = []
        row = []
        for i, unit_id in enumerate(available_units):
            unit = UNITS[unit_id]
            button = InlineKeyboardButton(
                unit["name"], 
                callback_data=f'{{"cmd":"train","id":"{unit_id}"}}'
            )
            row.append(button)
            
            # 2 buttons per row
            if (i + 1) % 2 == 0 or i == len(available_units) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        unit_list = "\n".join([
            f"• {UNITS[u_id]['name']} - " +
            f"Cost: {format_resources(UNITS[u_id]['base_cost'])}, " +
            f"Time: {format_time(UNITS[u_id]['train_time'])}"
            for u_id in available_units
        ])
        
        await update.message.reply_text(
            f"ℹ️ **Available Units:**\n{unit_list}\n\nSelect a unit to train:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Check tutorial progress
        if not player.get("tutorial_completed", False) and context.user_data.get("tutorial_step") == "first_build":
            context.user_data["tutorial_step"] = "train_instruction"
            await update.message.reply_text(
                "Perfect! Let's train some Sky Troopers to defend your base.\n\n"
                "Select Sky Trooper from the menu or use /train sky_trooper 2 to train 2 Sky Troopers."
            )
        
        return
    
    # Process training request with arguments
    unit_id = context.args[0].lower()
    quantity = 1
    
    # Check if quantity is specified
    if len(context.args) > 1:
        try:
            quantity = int(context.args[1])
            if not validate_quantity(quantity):
                await update.message.reply_text(MESSAGES["error_invalid_quantity"])
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid quantity. Must be a number.")
            return
    
    # Validate unit type
    if unit_id not in UNITS:
        await update.message.reply_text(MESSAGES["error_invalid_unit"])
        return
    
    # Check prerequisites
    if not await check_unit_prerequisites(player_id, unit_id):
        await update.message.reply_text(MESSAGES["error_prerequisites_not_met"])
        return
    
    # Try to add unit to queue
    result = await add_unit_to_queue(player_id, unit_id, quantity)
    if not result["success"]:
        await update.message.reply_text(f"❌ {result['message']}")
        return
    
    # Success
    unit_name = UNITS[unit_id]["name"]
    completion_time = format_time(result["train_time"])
    
    await update.message.reply_text(
        MESSAGES["success_train"].format(
            quantity=quantity,
            unit_name=unit_name,
            time=completion_time
        )
    )
    
    # Check tutorial progress
    if not player.get("tutorial_completed", False) and context.user_data.get("tutorial_step") == "train_instruction" and unit_id == "sky_trooper" and quantity >= 2:
        context.user_data["tutorial_step"] = "first_train"
        await update.message.reply_text(
            "Your Sky Troopers are being trained! They'll be ready to defend your base soon.\n\n"
            "Finally, let's set a name for your base. Use the /setname command followed by the name you want."
        )

async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /research command - research new technologies"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # If no arguments, show available research
    if not context.args:
        available_research = await get_available_research(player_id)
        
        if not available_research:
            await update.message.reply_text("❌ No technologies available to research. Build required buildings first.")
            return
        
        # Create keyboard with available research
        keyboard = []
        row = []
        for i, tech_id in enumerate(available_research):
            tech = RESEARCH[tech_id]
            button = InlineKeyboardButton(
                tech["name"], 
                callback_data=f'{{"cmd":"research","id":"{tech_id}"}}'
            )
            row.append(button)
            
            # 2 buttons per row
            if (i + 1) % 2 == 0 or i == len(available_research) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        research_list = "\n".join([
            f"• {RESEARCH[r_id]['name']} - " +
            f"Cost: {format_resources(RESEARCH[r_id]['base_cost'])}, " +
            f"Time: {format_time(RESEARCH[r_id]['research_time'])}"
            for r_id in available_research
        ])
        
        await update.message.reply_text(
            f"ℹ️ **Available Technologies:**\n{research_list}\n\nSelect a technology to research:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # Process research request with arguments
    tech_id = context.args[0].lower()
    
    # Validate technology
    if tech_id not in RESEARCH:
        await update.message.reply_text(MESSAGES["error_invalid_research"])
        return
    
    # Check prerequisites
    if not await check_research_prerequisites(player_id, tech_id):
        await update.message.reply_text(MESSAGES["error_prerequisites_not_met"])
        return
    
    # Try to add research to queue
    result = await add_research_to_queue(player_id, tech_id)
    if not result["success"]:
        await update.message.reply_text(f"❌ {result['message']}")
        return
    
    # Success
    tech_name = RESEARCH[tech_id]["name"]
    completion_time = format_time(result["research_time"])
    
    await update.message.reply_text(
        MESSAGES["success_research"].format(
            tech_name=tech_name,
            time=completion_time
        )
    )

async def unit_evolution_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /unit_evolution command - evolve units to higher tiers"""
    player = await ensure_player_exists(update, context)
    
    # Placeholder for unit evolution feature
    await update.message.reply_text(
        "ℹ️ Unit evolution will be available in a future update. Stay tuned, Commander!"
    )

async def defensive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /defensive command - manage defensive structures"""
    player = await ensure_player_exists(update, context)
    
    # Placeholder for defensive structures feature
    await update.message.reply_text(
        "ℹ️ Defensive structure management will be available in a future update. Stay tuned, Commander!"
    )

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /attack command - attack another player"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Missing target. Usage: /attack <player_id>")
        return
    
    target_id = context.args[0]
    
    # Validate target exists
    target = await get_player(target_id)
    if not target:
        await update.message.reply_text("❌ Target player not found.")
        return
    
    # Validate target is not self
    if target_id == player_id:
        await update.message.reply_text("❌ You cannot attack yourself.")
        return
    
    # Show attack confirmation with target info
    keyboard = [
        [
            InlineKeyboardButton("Confirm Attack", callback_data=f'{{"cmd":"attack","target":"{target_id}"}}'),
            InlineKeyboardButton("Cancel", callback_data='{"cmd":"cancel"}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ Preparing to attack {target['display_name']}.\n\n"
        f"Target power level: {target.get('power_level', 'Unknown')}\n"
        f"Your power level: {player.get('power_level', 'Unknown')}\n\n"
        f"Do you want to proceed with the attack?",
        reply_markup=reply_markup
    )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /scan command - find potential targets"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # Scan for potential targets
    targets = await scan_for_targets(player_id)
    
    if not targets:
        await update.message.reply_text("❌ No suitable targets found in scanning range.")
        return
    
    # Create paginated display of targets
    keyboard = []
    for target in targets[:5]:  # Show only top 5 targets
        button = InlineKeyboardButton(
            f"{target['display_name']} (Power: {target.get('power_level', 'Unknown')})",
            callback_data=f'{{"cmd":"attack","target":"{target["player_id"]}"}}'
        )
        keyboard.append([button])
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton("Cancel", callback_data='{"cmd":"cancel"}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "ℹ️ **Scan Results:**\n\nThe following targets were detected in range. Select one to attack:",
        reply_markup=reply_markup
    )

async def alliance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /alliance command - manage alliances"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    if not context.args:
        # Check if player is in an alliance
        alliance = await get_player_alliance(player_id)
        
        if alliance:
            # Show alliance info
            alliance_info = await get_alliance_info(alliance["alliance_id"])
            
            # Format alliance details
            member_count = len(alliance_info.get("members", []))
            founder = alliance_info.get("founder_name", "Unknown")
            created_date = alliance_info.get("created_date", "Unknown")
            
            alliance_details = (
                f"**Alliance: {alliance_info['name']}**\n"
                f"Members: {member_count}\n"
                f"Founder: {founder}\n"
                f"Created: {created_date}\n"
                f"Power Ranking: {alliance_info.get('power_ranking', 'Unranked')}\n\n"
                f"Use /alliance leave to leave this alliance."
            )
            
            await update.message.reply_text(
                MESSAGES["info_alliance"].format(alliance_details=alliance_details),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            # Show alliance options
            keyboard = [
                [
                    InlineKeyboardButton("Create Alliance", callback_data='{"cmd":"alliance","action":"create"}'),
                    InlineKeyboardButton("Join Alliance", callback_data='{"cmd":"alliance","action":"join"}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "You are not part of any alliance. Would you like to create a new alliance or join an existing one?",
                reply_markup=reply_markup
            )
        
        return
    
    # Process alliance subcommand
    subcommand = context.args[0].lower()
    
    if subcommand == "create":
        # Create a new alliance
        if len(context.args) < 2:
            await update.message.reply_text("❌ Missing alliance name. Usage: /alliance create <name>")
            return
        
        alliance_name = " ".join(context.args[1:])
        if not validate_name(alliance_name):
            await update.message.reply_text(MESSAGES["error_name_format"])
            return
        
        result = await create_alliance(player_id, alliance_name)
        if not result["success"]:
            await update.message.reply_text(f"❌ {result['message']}")
            return
        
        await update.message.reply_text(
            MESSAGES["success_alliance_create"].format(
                name=alliance_name,
                code=result["alliance_code"]
            )
        )
    
    elif subcommand == "join":
        # Join an existing alliance
        if len(context.args) < 2:
            await update.message.reply_text("❌ Missing alliance code. Usage: /alliance join <code>")
            return
        
        alliance_code = context.args[1]
        result = await join_alliance(player_id, alliance_code)
        if not result["success"]:
            await update.message.reply_text(f"❌ {result['message']}")
            return
        
        await update.message.reply_text(
            MESSAGES["success_alliance_join"].format(
                name=result["alliance_name"]
            )
        )
    
    elif subcommand == "leave":
        # Leave current alliance
        result = await leave_alliance(player_id)
        if not result["success"]:
            await update.message.reply_text(f"❌ {result['message']}")
            return
        
        await update.message.reply_text("✅ You have left your alliance.")
    
    elif subcommand == "info":
        # Get alliance info (can be used to look up other alliances)
        alliance_id = None
        if len(context.args) >= 2:
            alliance_id = context.args[1]
        else:
            # Get player's alliance
            alliance = await get_player_alliance(player_id)
            if alliance:
                alliance_id = alliance["alliance_id"]
        
        if not alliance_id:
            await update.message.reply_text("❌ You are not in an alliance. Join one first or specify an alliance ID.")
            return
        
        alliance_info = await get_alliance_info(alliance_id)
        if not alliance_info:
            await update.message.reply_text("❌ Alliance not found.")
            return
        
        # Format alliance details
        member_count = len(alliance_info.get("members", []))
        founder = alliance_info.get("founder_name", "Unknown")
        created_date = alliance_info.get("created_date", "Unknown")
        
        alliance_details = (
            f"**Alliance: {alliance_info['name']}**\n"
            f"Members: {member_count}\n"
            f"Founder: {founder}\n"
            f"Created: {created_date}\n"
            f"Power Ranking: {alliance_info.get('power_ranking', 'Unranked')}"
        )
        
        await update.message.reply_text(
            MESSAGES["info_alliance"].format(alliance_details=alliance_details),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    else:
        await update.message.reply_text(
            "❌ Invalid alliance subcommand. Available subcommands: create, join, leave, info"
        )

async def war_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /war command - manage alliance wars"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ Missing war subcommand. Available subcommands: create, join, deploy, status, results"
        )
        return
    
    subcommand = context.args[0].lower()
    
    if subcommand == "create":
        # Check if player is alliance leader
        alliance = await get_player_alliance(player_id)
        if not alliance or alliance.get("role") != "leader":
            await update.message.reply_text("❌ Only alliance leaders can start wars.")
            return
        
        # Placeholder for war creation
        await update.message.reply_text(
            "ℹ️ Alliance war creation will be available in a future update. Stay tuned, Commander!"
        )
    
    elif subcommand in ["join", "deploy", "status", "results"]:
        # Placeholder for other war subcommands
        await update.message.reply_text(
            "ℹ️ Alliance war features will be available in a future update. Stay tuned, Commander!"
        )
    
    else:
        await update.message.reply_text(
            "❌ Invalid war subcommand. Available subcommands: create, join, deploy, status, results"
        )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /leaderboard command - show rankings"""
    player = await ensure_player_exists(update, context)
    
    # Determine scope (global, alliance, faction)
    scope = "global"
    if context.args and context.args[0].lower() in ["global", "alliance", "faction"]:
        scope = context.args[0].lower()
    
    # Placeholder for leaderboard
    await update.message.reply_text(
        f"ℹ️ {scope.capitalize()} leaderboard will be available in a future update. Stay tuned, Commander!"
    )

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /daily command - claim daily login reward"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # Try to claim daily reward
    result = await claim_daily_reward(player_id)
    if not result["success"]:
        await update.message.reply_text(f"❌ {result['message']}")
        return
    
    # Format rewards
    rewards_text = ", ".join([f"{amount} {resource}" for resource, amount in result["rewards"].items()])
    
    # Add streak info if applicable
    streak_text = ""
    if result.get("streak", 0) > 1:
        streak_text = f"\nDaily streak: {result['streak']} days! ({result.get('streak_bonus', 0)}% bonus applied)"
    
    await update.message.reply_text(
        MESSAGES["success_daily"].format(rewards=rewards_text) + streak_text
    )

async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /achievements command - view and claim achievements"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # Get achievement progress
    achievements = await check_achievement_progress(player_id)
    
    if not achievements:
        await update.message.reply_text("❌ No achievements data available.")
        return
    
    # Create inline keyboard for claimable achievements
    keyboard = []
    claimable_found = False
    
    for ach_id, ach_data in achievements.items():
        if ach_data.get("can_claim", False):
            claimable_found = True
            button = InlineKeyboardButton(
                f"Claim: {ach_data['name']} Level {ach_data['level']}",
                callback_data=f'{{"cmd":"claim_achievement","id":"{ach_id}","level":{ach_data["level"]}}}'
            )
            keyboard.append([button])
    
    reply_markup = None
    if claimable_found:
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format achievements list
    achievements_list = ""
    for ach_id, ach_data in achievements.items():
        status = "✅ COMPLETED" if ach_data.get("completed", False) else f"Progress: {ach_data.get('progress', 0)}/{ach_data.get('target', 0)}"
        claimable = " (CLAIMABLE!)" if ach_data.get("can_claim", False) else ""
        
        achievements_list += f"• {ach_data['name']} Level {ach_data['level']}{claimable}\n  {status}\n"
    
    await update.message.reply_text(
        MESSAGES["info_achievements"].format(achievements_list=achievements_list),
        reply_markup=reply_markup
    )

async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /events command - show active events"""
    player = await ensure_player_exists(update, context)
    
    # Placeholder for events
    await update.message.reply_text(
        "ℹ️ Special events will be available in a future update. Stay tuned, Commander!"
    )

async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /notifications command - manage notifications settings"""
    player = await ensure_player_exists(update, context)
    
    if not context.args:
        # Show current notification settings
        keyboard = [
            [
                InlineKeyboardButton("Turn On All", callback_data='{"cmd":"notifications","action":"on_all"}'),
                InlineKeyboardButton("Turn Off All", callback_data='{"cmd":"notifications","action":"off_all"}')
            ],
            [
                InlineKeyboardButton("Buildings", callback_data='{"cmd":"notifications","type":"buildings"}'),
                InlineKeyboardButton("Units", callback_data='{"cmd":"notifications","type":"units"}')
            ],
            [
                InlineKeyboardButton("Research", callback_data='{"cmd":"notifications","type":"research"}'),
                InlineKeyboardButton("Attacks", callback_data='{"cmd":"notifications","type":"attacks"}')
            ],
            [
                InlineKeyboardButton("Alliance", callback_data='{"cmd":"notifications","type":"alliance"}'),
                InlineKeyboardButton("Events", callback_data='{"cmd":"notifications","type":"events"}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "ℹ️ **Notification Settings**\n\nChoose which notifications you want to receive:",
            reply_markup=reply_markup
        )
        return
    
    # Process notification toggle
    setting = context.args[0].lower()
    
    if setting in ["on", "off"]:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Missing notification type. Usage: /notifications on/off <type>")
            return
        
        notification_type = context.args[1].lower()
        # TODO: Implement notification settings
        await update.message.reply_text(
            f"✅ Notifications for {notification_type} turned {setting}."
        )
    else:
        await update.message.reply_text(
            "❌ Invalid setting. Use 'on' or 'off' followed by notification type."
        )

async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /tutorial command - start or skip tutorial"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    if not context.args:
        # Show tutorial options
        keyboard = [
            [
                InlineKeyboardButton("Start Tutorial", callback_data='{"cmd":"tutorial","action":"start"}'),
                InlineKeyboardButton("Skip Tutorial", callback_data='{"cmd":"tutorial","action":"skip"}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Would you like to start the tutorial or skip it?",
            reply_markup=reply_markup
        )
        return
    
    action = context.args[0].lower()
    
    if action == "start":
        # Start the tutorial
        context.user_data["tutorial_step"] = "welcome"
        await update.message.reply_text(MESSAGES["tutorial_start"])
        
        # Send the first tutorial message
        await update.message.reply_text(
            "Welcome to SkyHustle, Commander! I'll guide you through the basics of managing your aerial base. Let's get started!\n\n"
            "First, check your base status with the /status command."
        )
    
    elif action == "skip":
        # Skip the tutorial
        # Mark tutorial as completed in player data
        await update.player(player_id, {"tutorial_completed": True})
        await update.message.reply_text(MESSAGES["tutorial_skip"])
    
    else:
        await update.message.reply_text(
            "❌ Invalid tutorial command. Use '/tutorial start' or '/tutorial skip'."
        )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /weather command - show random weather condition"""
    player = await ensure_player_exists(update, context)
    
    # Select a random weather message
    weather_message = random.choice(WEATHER_MESSAGES)
    
    await update.message.reply_text(f"🌤️ **Weather Report:**\n\n{weather_message}")

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /save command - force save data to Google Sheets"""
    player = await ensure_player_exists(update, context)
    
    # Check if user is admin (for now, everyone can use this)
    try:
        await save_data()
        await update.message.reply_text("✅ Game data saved successfully.")
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        await update.message.reply_text(f"❌ Error saving data: {str(e)}")

async def load_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /load command - force load data from Google Sheets"""
    player = await ensure_player_exists(update, context)
    
    # Check if user is admin (for now, everyone can use this)
    try:
        await load_data()
        await update.message.reply_text("✅ Game data loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        await update.message.reply_text(f"❌ Error loading data: {str(e)}")

async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /setname command - set player's display name"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Missing name. Usage: /setname <name>")
        return
    
    new_name = " ".join(context.args)
    
    # Validate name
    if not validate_name(new_name):
        await update.message.reply_text(MESSAGES["error_name_format"])
        return
    
    if len(new_name) > 32:
        await update.message.reply_text(
            MESSAGES["error_name_too_long"].format(max_length=32)
        )
        return
    
    # Check if name is unique
    if not await is_name_unique(new_name, player_id):
        await update.message.reply_text(MESSAGES["error_name_taken"])
        return
    
    # Update player name
    await update_player(player_id, {"display_name": new_name})
    
    await update.message.reply_text(
        MESSAGES["success_name_set"].format(name=new_name)
    )
    
    # Check tutorial progress
    if not player.get("tutorial_completed", False) and context.user_data.get("tutorial_step") == "first_train":
        context.user_data["tutorial_step"] = "set_name"
        
        # Complete tutorial and give rewards
        bonus_resources = {
            "credits": 200,
            "minerals": 100,
            "energy": 100
        }
        
        await update_player(player_id, {
            "tutorial_completed": True,
            "credits": player.get("credits", 0) + bonus_resources["credits"],
            "minerals": player.get("minerals", 0) + bonus_resources["minerals"],
            "energy": player.get("energy", 0) + bonus_resources["energy"]
        })
        
        bonus_text = f"Credits: +{bonus_resources['credits']}, Minerals: +{bonus_resources['minerals']}, Energy: +{bonus_resources['energy']}"
        
        await update.message.reply_text(
            f"Perfect! Your base now has a name that will be displayed to other players.\n\n"
            f"You've completed the basic tutorial! Here's a bonus of resources to help you get started:\n"
            f"{bonus_text}\n\n"
            f"You can check your updated status with /status or explore other commands with /help."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command - show available commands"""
    player = await ensure_player_exists(update, context)
    
    commands_list = (
        "**Basic Commands:**\n"
        "• /start - Start the game or get welcome message\n"
        "• /status - View your base status and resources\n"
        "• /help - Show this help message\n\n"
        
        "**Building & Training:**\n"
        "• /build [building] [quantity] - Build structures\n"
        "• /train [unit] [count] - Train units\n\n"
        
        "**Research & Development:**\n"
        "• /research [tech_id] - Research technologies\n"
        "• /unit_evolution - Evolve units to higher tiers\n\n"
        
        "**Combat & Defense:**\n"
        "• /defensive - Manage defensive structures\n"
        "• /attack <player_id> - Attack another player\n"
        "• /scan - Find potential targets\n\n"
        
        "**Alliances & Wars:**\n"
        "• /alliance <subcmd> - Manage alliances\n"
        "• /war <subcmd> - Alliance war commands\n\n"
        
        "**Progression & Rewards:**\n"
        "• /leaderboard [scope] - View rankings\n"
        "• /daily - Claim daily login reward\n"
        "• /achievements - View and claim achievements\n"
        "• /events - View active events\n\n"
        
        "**Settings & Utilities:**\n"
        "• /notifications [on/off] [type] - Manage notifications\n"
        "• /tutorial [start/skip] - Start or skip tutorial\n"
        "• /weather - Get fun atmospheric conditions\n"
        "• /setname <name> - Set your display name\n"
        "• /save - Force save game data\n"
        "• /load - Force load game data"
    )
    
    await update.message.reply_text(
        MESSAGES["info_help"].format(commands_list=commands_list),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /admin command - admin-only commands"""
    player = await ensure_player_exists(update, context)
    player_id = str(update.effective_user.id)
    
    # Check if user is admin (for development purposes)
    admin_ids = os.getenv("ADMIN_IDS", "").split(",")
    if player_id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to use admin commands.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "ℹ️ **Admin Commands:**\n"
            "• /admin stats - Show game statistics\n"
            "• /admin reset <player_id> - Reset a player's data\n"
            "• /admin give <player_id> <resource> <amount> - Give resources to a player\n"
            "• /admin broadcast <message> - Send message to all players"
        )
        return
    
    subcommand = context.args[0].lower()
    
    if subcommand == "stats":
        # Show game statistics
        await update.message.reply_text("ℹ️ Game statistics will be available in a future update.")
    
    elif subcommand == "reset":
        if len(context.args) < 2:
            await update.message.reply_text("❌ Missing player ID. Usage: /admin reset <player_id>")
            return
        
        target_id = context.args[1]
        # TODO: Implement player reset
        await update.message.reply_text(f"✅ Player {target_id} has been reset.")
    
    elif subcommand == "give":
        if len(context.args) < 4:
            await update.message.reply_text("❌ Missing arguments. Usage: /admin give <player_id> <resource> <amount>")
            return
        
        target_id = context.args[1]
        resource = context.args[2].lower()
        
        try:
            amount = int(context.args[3])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number.")
            return
        
        # TODO: Implement resource giving
        await update.message.reply_text(f"✅ Gave {amount} {resource} to player {target_id}.")
    
    elif subcommand == "broadcast":
        if len(context.args) < 2:
            await update.message.reply_text("❌ Missing message. Usage: /admin broadcast <message>")
            return
        
        message = " ".join(context.args[1:])
        # TODO: Implement broadcast
        await update.message.reply_text(f"✅ Broadcast message sent: \"{message}\"")
    
    else:
        await update.message.reply_text("❌ Invalid admin subcommand.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in command processing"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        # Send error message to user
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred while processing your command. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
