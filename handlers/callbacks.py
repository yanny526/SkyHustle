"""
Callback query handlers for the SkyHustle Telegram bot
Handles all callbacks from inline keyboards
"""
import json
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants import BUILDINGS, UNITS, RESEARCH
from modules.player import get_player, update_player, claim_achievement
from modules.buildings import add_building_to_queue
from modules.units import add_unit_to_queue
from modules.research import add_research_to_queue
from modules.alliance import create_alliance, join_alliance
from modules.battles import attack_player

from handlers.tutorial import start_tutorial, skip_tutorial
from utils.formatting import format_time, format_resources
from utils.logger import get_logger

logger = get_logger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    
    # Acknowledge the callback query
    await query.answer()
    
    try:
        # Parse the callback data
        data = json.loads(query.data)
        cmd = data.get("cmd")
        
        if not cmd:
            logger.error(f"Invalid callback data: {query.data}")
            await query.edit_message_text("❌ Invalid callback data. Please try again.")
            return
        
        # Route to the appropriate handler based on command
        if cmd == "build":
            await handle_build_callback(update, context, data)
        elif cmd == "train":
            await handle_train_callback(update, context, data)
        elif cmd == "research":
            await handle_research_callback(update, context, data)
        elif cmd == "attack":
            await handle_attack_callback(update, context, data)
        elif cmd == "alliance":
            await handle_alliance_callback(update, context, data)
        elif cmd == "claim_achievement":
            await handle_claim_achievement_callback(update, context, data)
        elif cmd == "tutorial":
            await handle_tutorial_callback(update, context, data)
        elif cmd == "notifications":
            await handle_notifications_callback(update, context, data)
        elif cmd == "cancel":
            await handle_cancel_callback(update, context, data)
        else:
            logger.warning(f"Unknown callback command: {cmd}")
            await query.edit_message_text("❌ Unknown command. Please try again.")
    
    except json.JSONDecodeError:
        logger.error(f"Failed to parse callback data: {query.data}")
        await query.edit_message_text("❌ Error processing request. Please try again.")
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again later.")

async def handle_build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle building selection from inline keyboard"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    building_id = data.get("id")
    
    if not building_id or building_id not in BUILDINGS:
        await query.edit_message_text("❌ Invalid building selection.")
        return
    
    # Show building details and quantity selection
    building = BUILDINGS[building_id]
    
    # Create quantity selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data=f'{{"cmd":"build_confirm","id":"{building_id}","qty":1}}'),
            InlineKeyboardButton("5", callback_data=f'{{"cmd":"build_confirm","id":"{building_id}","qty":5}}'),
            InlineKeyboardButton("10", callback_data=f'{{"cmd":"build_confirm","id":"{building_id}","qty":10}}')
        ],
        [
            InlineKeyboardButton("Build 1", callback_data=f'{{"cmd":"build_confirm","id":"{building_id}","qty":1}}')
        ],
        [
            InlineKeyboardButton("« Back", callback_data='{"cmd":"build_list"}'),
            InlineKeyboardButton("Cancel", callback_data='{"cmd":"cancel"}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format building details
    provides = "\n".join([f"• {key}: {value}" for key, value in building["provides"].items()])
    prerequisites = "\n".join([f"• {BUILDINGS[req]['name']} Level {level}" for req, level in building["prerequisites"].items()]) if building["prerequisites"] else "None"
    
    message = (
        f"**{building['name']}**\n"
        f"{building['description']}\n\n"
        f"**Cost:**\n"
        f"{format_resources(building['base_cost'])}\n\n"
        f"**Build Time:** {format_time(building['build_time'])}\n\n"
        f"**Provides:**\n{provides}\n\n"
        f"**Prerequisites:**\n{prerequisites}\n\n"
        f"Select quantity to build:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_train_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle unit selection from inline keyboard"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    unit_id = data.get("id")
    
    if not unit_id or unit_id not in UNITS:
        await query.edit_message_text("❌ Invalid unit selection.")
        return
    
    # Show unit details and quantity selection
    unit = UNITS[unit_id]
    
    # Create quantity selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data=f'{{"cmd":"train_confirm","id":"{unit_id}","qty":1}}'),
            InlineKeyboardButton("5", callback_data=f'{{"cmd":"train_confirm","id":"{unit_id}","qty":5}}'),
            InlineKeyboardButton("10", callback_data=f'{{"cmd":"train_confirm","id":"{unit_id}","qty":10}}')
        ],
        [
            InlineKeyboardButton("Train 1", callback_data=f'{{"cmd":"train_confirm","id":"{unit_id}","qty":1}}')
        ],
        [
            InlineKeyboardButton("« Back", callback_data='{"cmd":"train_list"}'),
            InlineKeyboardButton("Cancel", callback_data='{"cmd":"cancel"}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format unit details
    stats = "\n".join([f"• {key.capitalize()}: {value}" for key, value in unit["stats"].items()])
    prerequisites = "\n".join([f"• {BUILDINGS[req]['name']} Level {level}" for req, level in unit["prerequisites"].items()]) if unit["prerequisites"] else "None"
    
    message = (
        f"**{unit['name']}**\n"
        f"{unit['description']}\n\n"
        f"**Cost:**\n"
        f"{format_resources(unit['base_cost'])}\n\n"
        f"**Training Time:** {format_time(unit['train_time'])}\n\n"
        f"**Stats:**\n{stats}\n\n"
        f"**Prerequisites:**\n{prerequisites}\n\n"
        f"Select quantity to train:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle research selection from inline keyboard"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    tech_id = data.get("id")
    
    if not tech_id or tech_id not in RESEARCH:
        await query.edit_message_text("❌ Invalid technology selection.")
        return
    
    # Show research details and confirmation
    tech = RESEARCH[tech_id]
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("Research", callback_data=f'{{"cmd":"research_confirm","id":"{tech_id}"}}'),
            InlineKeyboardButton("Cancel", callback_data='{"cmd":"cancel"}')
        ],
        [
            InlineKeyboardButton("« Back", callback_data='{"cmd":"research_list"}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format research details
    effects = ""
    for level, effect in tech["level_effects"].items():
        level_effects = "\n".join([f"• {key.replace('_', ' ').capitalize()}: {value}" for key, value in effect.items()])
        effects += f"**Level {level}:**\n{level_effects}\n\n"
    
    prerequisites = "\n".join([f"• {BUILDINGS[req]['name'] if req in BUILDINGS else RESEARCH[req]['name']} Level {level}" for req, level in tech["prerequisites"].items()]) if tech["prerequisites"] else "None"
    
    message = (
        f"**{tech['name']}**\n"
        f"{tech['description']}\n\n"
        f"**Cost:**\n"
        f"{format_resources(tech['base_cost'])}\n\n"
        f"**Research Time:** {format_time(tech['research_time'])}\n\n"
        f"**Effects:**\n{effects}\n"
        f"**Prerequisites:**\n{prerequisites}\n\n"
        f"Would you like to research this technology?"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_attack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle attack confirmation from inline keyboard"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    target_id = data.get("target")
    
    if not target_id:
        await query.edit_message_text("❌ Invalid target selection.")
        return
    
    # Execute attack
    result = await attack_player(player_id, target_id)
    
    if not result["success"]:
        await query.edit_message_text(f"❌ Attack failed: {result['message']}")
        return
    
    # Show battle results
    battle_report = result.get("battle_report", {})
    target_name = battle_report.get("defender_name", "Unknown")
    outcome = battle_report.get("outcome", "Unknown")
    resources_gained = battle_report.get("resources_gained", {})
    experience_gained = battle_report.get("experience_gained", 0)
    
    resources_text = ", ".join([f"{amount} {resource}" for resource, amount in resources_gained.items()]) if resources_gained else "None"
    
    message = (
        f"**Battle Report**\n\n"
        f"Target: {target_name}\n"
        f"Outcome: {outcome}\n"
        f"Resources gained: {resources_text}\n"
        f"Experience gained: {experience_gained}\n\n"
        f"Detailed report:\n{battle_report.get('details', 'No details available.')}"
    )
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown"
    )

async def handle_alliance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle alliance-related callbacks"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    action = data.get("action")
    
    if action == "create":
        # Show alliance creation form
        await query.edit_message_text(
            "To create an alliance, use the command:\n"
            "/alliance create <alliance_name>\n\n"
            "Example: /alliance create Sky Warriors"
        )
    
    elif action == "join":
        # Show alliance join form
        await query.edit_message_text(
            "To join an alliance, use the command:\n"
            "/alliance join <alliance_code>\n\n"
            "You need an invitation code from an existing alliance member."
        )
    
    else:
        await query.edit_message_text("❌ Invalid alliance action.")

async def handle_claim_achievement_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle achievement claim from inline keyboard"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    achievement_id = data.get("id")
    achievement_level = data.get("level")
    
    if not achievement_id or not achievement_level:
        await query.edit_message_text("❌ Invalid achievement selection.")
        return
    
    # Claim the achievement
    result = await claim_achievement(player_id, achievement_id, achievement_level)
    
    if not result["success"]:
        await query.edit_message_text(f"❌ Failed to claim achievement: {result['message']}")
        return
    
    # Show reward details
    rewards = result.get("rewards", {})
    rewards_text = ", ".join([f"{amount} {resource}" for resource, amount in rewards.items()]) if rewards else "None"
    
    message = (
        f"✅ Achievement claimed: {result.get('name', 'Achievement')} Level {achievement_level}\n\n"
        f"Rewards received: {rewards_text}\n\n"
        f"Check your updated achievements with /achievements"
    )
    
    await query.edit_message_text(message)

async def handle_tutorial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle tutorial start/skip from inline keyboard"""
    query = update.callback_query
    action = data.get("action")
    
    if action == "start":
        await start_tutorial(update, context)
    elif action == "skip":
        await skip_tutorial(update, context)
    else:
        await query.edit_message_text("❌ Invalid tutorial action.")

async def handle_notifications_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle notification settings from inline keyboard"""
    query = update.callback_query
    player_id = str(update.effective_user.id)
    action = data.get("action")
    notification_type = data.get("type")
    
    if action in ["on_all", "off_all"]:
        # Toggle all notifications
        enabled = action == "on_all"
        # TODO: Implement notification settings update
        await query.edit_message_text(f"✅ All notifications turned {'on' if enabled else 'off'}.")
    
    elif notification_type:
        # Toggle specific notification type
        # TODO: Implement notification type toggle
        keyboard = [
            [
                InlineKeyboardButton("Turn On", callback_data=f'{{"cmd":"notifications","type":"{notification_type}","action":"on"}}'),
                InlineKeyboardButton("Turn Off", callback_data=f'{{"cmd":"notifications","type":"{notification_type}","action":"off"}}')
            ],
            [
                InlineKeyboardButton("« Back", callback_data='{"cmd":"notifications"}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Notification settings for: {notification_type.capitalize()}\n\n"
            f"Current status: Unknown\n\n"
            f"Choose an option:",
            reply_markup=reply_markup
        )
    
    else:
        await query.edit_message_text("❌ Invalid notification action.")

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Handle cancel button from inline keyboard"""
    query = update.callback_query
    
    await query.edit_message_text("Operation cancelled.")
