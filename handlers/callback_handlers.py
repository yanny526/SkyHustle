"""
Callback query handlers for the SkyHustle Telegram bot.
Handles all inline button interactions.
"""
import json
import logging
from typing import Dict, Any, Tuple, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from modules.player import player_exists, get_player, create_player
from modules.building import queue_building, get_available_buildings
from modules.unit import train_units, get_available_units
from modules.research import research_technology, get_available_technologies
from modules.battle import attack_player, scan_for_targets
from modules.alliance import (
    create_alliance,
    join_alliance,
    leave_alliance,
    invite_to_alliance,
    get_alliance_info,
    disband_alliance,
)
from utils.helpers import decode_callback_data, encode_callback_data

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from inline keyboard buttons.
    
    Args:
        update: The update containing the callback query
        context: The context object
    """
    query = update.callback_query
    
    try:
        # Attempt to decode the callback data
        callback_type, callback_data = decode_callback_data(query.data)
        
        # Log the callback for debugging
        logging.debug(f"Callback received: {callback_type} with data {callback_data}")
        
        # Handle different callback types
        if callback_type == "tutorial":
            await handle_tutorial_callback(update, context, callback_data)
        elif callback_type == "action":
            await handle_action_callback(update, context, callback_data)
        elif callback_type == "build":
            await handle_build_callback(update, context, callback_data)
        elif callback_type == "train":
            await handle_train_callback(update, context, callback_data)
        elif callback_type == "research":
            await handle_research_callback(update, context, callback_data)
        elif callback_type == "attack_confirm":
            await handle_attack_confirm_callback(update, context, callback_data)
        elif callback_type == "attack_cancel":
            await handle_attack_cancel_callback(update, context, callback_data)
        elif callback_type == "attack_target":
            await handle_attack_target_callback(update, context, callback_data)
        elif callback_type == "alliance":
            await handle_alliance_callback(update, context, callback_data)
        else:
            # Unknown callback type
            await query.answer(f"Unknown callback type: {callback_type}")
            return
        
    except Exception as e:
        logging.error(f"Error handling callback query: {e}", exc_info=True)
        await query.answer("An error occurred processing your request.")
        return

async def handle_tutorial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle tutorial-related callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    action = data.get("action", "")
    
    if action == "start":
        # Start the tutorial
        await query.edit_message_text(
            "🎮 *Tutorial Starting*\n\n"
            "Welcome to SkyHustle! Let me guide you through the basics.\n\n"
            "First, let's check your base status. Type /status to see your resources and base information.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Set the player's tutorial state
        player = await get_player(user_id)
        player.tutorial_state = "status"
        await player.save()
        
    elif action == "skip":
        # Skip the tutorial
        await query.edit_message_text(
            "✅ *Tutorial Skipped*\n\n"
            "You've chosen to skip the tutorial. You can always restart it with /tutorial start.\n\n"
            "Use /status to check your base and /help to see available commands.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Mark tutorial as completed
        player = await get_player(user_id)
        player.tutorial_completed = True
        await player.save()
    
    await query.answer()

async def handle_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle action-related callbacks (build, train, research).
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    action_type = data.get("type", "")
    
    if action_type == "build":
        # Show available buildings
        available_buildings = await get_available_buildings(user_id)
        
        # Create buttons for available buildings
        keyboard = []
        for i in range(0, len(available_buildings), 2):
            row = []
            for j in range(2):
                if i + j < len(available_buildings):
                    building = available_buildings[i + j]
                    callback_data = encode_callback_data(
                        "build", {"id": building["id"]}
                    )
                    row.append(InlineKeyboardButton(
                        f"{building['name']} ({building['cost']} 💰)",
                        callback_data=callback_data
                    ))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton("◀️ Back", callback_data=encode_callback_data("action", {"type": "back"}))
        ])
        
        await query.edit_message_text(
            "🏗️ *Available Buildings:*\n"
            "Select a building to construct:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action_type == "train":
        # Show available units
        available_units = await get_available_units(user_id)
        
        # Create buttons for available units
        keyboard = []
        for i in range(0, len(available_units), 2):
            row = []
            for j in range(2):
                if i + j < len(available_units):
                    unit = available_units[i + j]
                    callback_data = encode_callback_data(
                        "train", {"id": unit["id"]}
                    )
                    row.append(InlineKeyboardButton(
                        f"{unit['name']} ({unit['cost']} 💰)",
                        callback_data=callback_data
                    ))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton("◀️ Back", callback_data=encode_callback_data("action", {"type": "back"}))
        ])
        
        await query.edit_message_text(
            "⚔️ *Available Units:*\n"
            "Select a unit to train:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action_type == "research":
        # Show available technologies
        available_techs = await get_available_technologies(user_id)
        
        # Create buttons for available technologies
        keyboard = []
        for i in range(0, len(available_techs), 2):
            row = []
            for j in range(2):
                if i + j < len(available_techs):
                    tech = available_techs[i + j]
                    callback_data = encode_callback_data(
                        "research", {"id": tech["id"]}
                    )
                    row.append(InlineKeyboardButton(
                        f"{tech['name']} ({tech['cost']} 💰)",
                        callback_data=callback_data
                    ))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton("◀️ Back", callback_data=encode_callback_data("action", {"type": "back"}))
        ])
        
        await query.edit_message_text(
            "🔬 *Available Technologies:*\n"
            "Select a technology to research:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action_type == "back":
        # Go back to status
        player = await get_player(user_id)
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("🏗️ Build", callback_data=encode_callback_data("action", {"type": "build"})),
                InlineKeyboardButton("⚔️ Train", callback_data=encode_callback_data("action", {"type": "train"})),
                InlineKeyboardButton("🔬 Research", callback_data=encode_callback_data("action", {"type": "research"}))
            ]
        ]
        
        # Update message with status and action buttons
        await query.edit_message_text(
            f"*Base Status for {player.display_name}*\n\n"
            f"💰 Credits: {player.credits}\n"
            f"🪨 Minerals: {player.minerals}\n"
            f"⚡ Energy: {player.energy}\n"
            f"💎 SkyBucks: {player.skybucks}\n\n"
            f"🌟 Experience: {player.experience}",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    await query.answer()

async def handle_build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle building-related callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    building_id = data.get("id", "")
    quantity = data.get("qty", 1)
    
    # Queue the building
    result = await queue_building(user_id, building_id, quantity)
    
    if result["success"]:
        await query.answer(f"Building queued: {result['message']}")
        
        # Update the message to show success
        await query.edit_message_text(
            f"✅ {result['message']}\n\n"
            "What would you like to do next?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏗️ Build More", callback_data=encode_callback_data("action", {"type": "build"})),
                    InlineKeyboardButton("📊 Status", callback_data=encode_callback_data("action", {"type": "back"}))
                ]
            ])
        )
    else:
        await query.answer(f"Error: {result['message']}")

async def handle_train_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle unit training-related callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    unit_id = data.get("id", "")
    count = data.get("count", 1)
    
    # Train the units
    result = await train_units(user_id, unit_id, count)
    
    if result["success"]:
        await query.answer(f"Units queued: {result['message']}")
        
        # Update the message to show success
        await query.edit_message_text(
            f"✅ {result['message']}\n\n"
            "What would you like to do next?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚔️ Train More", callback_data=encode_callback_data("action", {"type": "train"})),
                    InlineKeyboardButton("📊 Status", callback_data=encode_callback_data("action", {"type": "back"}))
                ]
            ])
        )
    else:
        await query.answer(f"Error: {result['message']}")

async def handle_research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle technology research-related callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    tech_id = data.get("id", "")
    
    # Research the technology
    result = await research_technology(user_id, tech_id)
    
    if result["success"]:
        await query.answer(f"Technology researched: {result['message']}")
        
        # Update the message to show success
        await query.edit_message_text(
            f"✅ {result['message']}\n\n"
            "What would you like to do next?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔬 Research More", callback_data=encode_callback_data("action", {"type": "research"})),
                    InlineKeyboardButton("📊 Status", callback_data=encode_callback_data("action", {"type": "back"}))
                ]
            ])
        )
    else:
        await query.answer(f"Error: {result['message']}")

async def handle_attack_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle attack confirmation callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    target_id = data.get("target", 0)
    
    # Execute the attack
    result = await attack_player(user_id, target_id)
    
    if result["success"]:
        # Update the message with battle results
        await query.edit_message_text(
            f"⚔️ *Battle Results*\n\n{result['message']}",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Scan Again", callback_data=encode_callback_data("action", {"type": "scan"})),
                    InlineKeyboardButton("📊 Status", callback_data=encode_callback_data("action", {"type": "back"}))
                ]
            ])
        )
    else:
        await query.answer(f"Attack failed: {result['message']}")
    
    await query.answer()

async def handle_attack_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle attack cancellation callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    
    await query.edit_message_text(
        "Attack cancelled. Your forces remain at your base."
    )
    
    await query.answer()

async def handle_attack_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle attack target selection callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    target_id = data.get("id", 0)
    
    # Ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm Attack",
                callback_data=encode_callback_data("attack_confirm", {"target": target_id})
            ),
            InlineKeyboardButton(
                "Cancel",
                callback_data=encode_callback_data("attack_cancel", {})
            )
        ]
    ]
    
    await query.edit_message_text(
        f"⚠️ Are you sure you want to attack player {target_id}?\n"
        "This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await query.answer()

async def handle_alliance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]) -> None:
    """
    Handle alliance-related callbacks.
    
    Args:
        update: The update containing the callback query
        context: The context object
        data: The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if the player exists
    if not await player_exists(user_id):
        await query.answer("You need to start the game first. Use /start command.")
        return
    
    action = data.get("action", "")
    
    if action == "create_prompt":
        # Prompt for alliance name
        await query.edit_message_text(
            "📝 *Create Alliance*\n\n"
            "Please enter a name for your alliance using the command:\n"
            "/alliance create <name>",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    elif action == "join_prompt":
        # Prompt for alliance code
        await query.edit_message_text(
            "🔑 *Join Alliance*\n\n"
            "Please enter the alliance join code using the command:\n"
            "/alliance join <code>",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    elif action == "info":
        # Get alliance info
        alliance_info = await get_alliance_info(user_id)
        if alliance_info:
            # Format alliance info
            message = (
                f"🛡️ *Alliance: {alliance_info['name']}*\n\n"
                f"👑 Leader: {alliance_info['leader_name']}\n"
                f"👥 Members: {alliance_info['member_count']}\n"
                f"🏆 Power Ranking: {alliance_info['power_ranking']}\n\n"
                f"Join Code: `{alliance_info['join_code']}`"
            )
            
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await query.edit_message_text(
                "❌ You are not in an alliance.\n\n"
                "You can create or join an alliance using the /alliance command."
            )
        
    elif action == "leave_confirm":
        # Confirm leaving alliance
        keyboard = [
            [
                InlineKeyboardButton(
                    "Confirm Leave",
                    callback_data=encode_callback_data("alliance", {"action": "leave_execute"})
                ),
                InlineKeyboardButton(
                    "Cancel",
                    callback_data=encode_callback_data("alliance", {"action": "info"})
                )
            ]
        ]
        
        await query.edit_message_text(
            "⚠️ Are you sure you want to leave your alliance?\n"
            "This action cannot be undone.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action == "leave_execute":
        # Execute leave alliance
        result = await leave_alliance(user_id)
        
        if result["success"]:
            await query.edit_message_text(
                f"✅ {result['message']}"
            )
        else:
            await query.edit_message_text(
                f"❌ {result['message']}"
            )
        
    elif action == "invite_prompt":
        # Prompt for player username
        await query.edit_message_text(
            "👤 *Invite Player*\n\n"
            "Please enter the username of the player you want to invite using the command:\n"
            "/alliance invite @username",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    elif action == "disband_confirm":
        # Confirm disbanding alliance
        keyboard = [
            [
                InlineKeyboardButton(
                    "Confirm Disband",
                    callback_data=encode_callback_data("alliance", {"action": "disband_execute"})
                ),
                InlineKeyboardButton(
                    "Cancel",
                    callback_data=encode_callback_data("alliance", {"action": "info"})
                )
            ]
        ]
        
        await query.edit_message_text(
            "⚠️ Are you sure you want to disband your alliance?\n"
            "This action cannot be undone and will remove all members!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action == "disband_execute":
        # Execute disband alliance
        result = await disband_alliance(user_id)
        
        if result["success"]:
            await query.edit_message_text(
                f"✅ {result['message']}"
            )
        else:
            await query.edit_message_text(
                f"❌ {result['message']}"
            )
    
    await query.answer()
