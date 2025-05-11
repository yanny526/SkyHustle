"""
Formatting utilities for the SkyHustle Telegram bot.
Handles message formatting for different response types.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from modules.player import Player
from modules.building import BuildQueue, get_building_info
from modules.unit import TrainingQueue, get_unit_info
from modules.research import get_research_info

async def format_status_message(player: Player, build_queue: List[BuildQueue], training_queue: List[TrainingQueue]) -> str:
    """
    Format a player's status message with resources, queues, and stats.
    
    Args:
        player: Player object
        build_queue: List of BuildQueue objects
        training_queue: List of TrainingQueue objects
    
    Returns:
        Formatted status message with Markdown
    """
    # Escape player name for Markdown V2
    player_name = escape_markdown(player.display_name, version=2)
    
    # Format resources with emoji
    resources = (
        f"💰 Credits: {player.credits}\n"
        f"🪨 Minerals: {player.minerals}\n"
        f"⚡ Energy: {player.energy}\n"
        f"💎 SkyBucks: {player.skybucks}\n"
    )
    
    # Format experience
    experience = f"🌟 Experience: {player.experience}\n"
    
    # Format build queue
    build_queue_text = ""
    if build_queue:
        build_queue_text = "\n*Building Queue:*\n"
        for i, item in enumerate(build_queue, 1):
            building_info = await get_building_info(item.building_id)
            building_name = escape_markdown(building_info["name"], version=2)
            remaining_time = calculate_remaining_time(item.end_time)
            
            completed = f"{item.completed}/{item.quantity}" if item.quantity > 1 else ""
            
            build_queue_text += f"{i}\\. {building_name} {completed} \\- {remaining_time}\n"
    
    # Format training queue
    training_queue_text = ""
    if training_queue:
        training_queue_text = "\n*Training Queue:*\n"
        for i, item in enumerate(training_queue, 1):
            unit_info = await get_unit_info(item.unit_id)
            unit_name = escape_markdown(unit_info["name"], version=2)
            remaining_time = calculate_remaining_time(item.end_time)
            
            completed = f"{item.completed}/{item.quantity}" if item.quantity > 1 else ""
            
            training_queue_text += f"{i}\\. {unit_name} {completed} \\- {remaining_time}\n"
    
    # Combine all sections
    status_message = (
        f"*Base Status for {player_name}*\n\n"
        f"{resources}\n"
        f"{experience}"
        f"{build_queue_text}"
        f"{training_queue_text}"
    )
    
    return status_message

def calculate_remaining_time(end_time: datetime) -> str:
    """
    Calculate and format the remaining time until a datetime.
    
    Args:
        end_time: The target datetime
    
    Returns:
        Formatted time string (e.g., "2h 30m")
    """
    now = datetime.now()
    
    if end_time <= now:
        return "Completed"
    
    remaining = end_time - now
    
    # Format based on remaining time
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def format_building_info(building_id: str) -> str:
    """
    Format building information for display.
    
    Args:
        building_id: The building ID
    
    Returns:
        Formatted building information
    """
    try:
        building_info = await get_building_info(building_id)
        
        name = escape_markdown(building_info["name"], version=2)
        description = escape_markdown(building_info["description"], version=2)
        
        # Format requirements
        requirements_text = ""
        if building_info["requirements"]:
            req_names = []
            for req_id in building_info["requirements"]:
                req_info = await get_building_info(req_id)
                req_names.append(escape_markdown(req_info["name"], version=2))
            
            requirements_text = f"*Requires:* {', '.join(req_names)}\n"
        
        # Format provides
        provides_text = ""
        if "provides" in building_info and building_info["provides"]:
            provides = []
            for key, value in building_info["provides"].items():
                provides.append(f"{key.replace('_', ' ').title()}: {value}")
            
            provides_text = f"*Provides:* {', '.join(provides)}\n"
        
        # Format cost
        cost_text = (
            f"*Cost:* 💰 {building_info['cost']} Credits, "
            f"🪨 {building_info['minerals']} Minerals, "
            f"⚡ {building_info['energy']} Energy\n"
        )
        
        # Format build time
        build_time = building_info["build_time"]
        minutes, seconds = divmod(build_time, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            build_time_text = f"*Build Time:* {hours}h {minutes}m\n"
        else:
            build_time_text = f"*Build Time:* {minutes}m {seconds}s\n"
        
        # Combine all sections
        building_text = (
            f"*{name}*\n\n"
            f"{description}\n\n"
            f"{cost_text}"
            f"{build_time_text}"
            f"{requirements_text}"
            f"{provides_text}"
        )
        
        return building_text
    
    except Exception as e:
        logging.error(f"Error formatting building info: {e}", exc_info=True)
        return f"Error retrieving building information for {building_id}."

async def format_unit_info(unit_id: str) -> str:
    """
    Format unit information for display.
    
    Args:
        unit_id: The unit ID
    
    Returns:
        Formatted unit information
    """
    try:
        unit_info = await get_unit_info(unit_id)
        
        name = escape_markdown(unit_info["name"], version=2)
        description = escape_markdown(unit_info["description"], version=2)
        
        # Format requirements
        requirements_text = ""
        if unit_info["requirements"]:
            req_names = []
            for req_id in unit_info["requirements"]:
                req_info = await get_building_info(req_id)
                req_names.append(escape_markdown(req_info["name"], version=2))
            
            requirements_text = f"*Requires:* {', '.join(req_names)}\n"
        
        # Format stats
        stats_text = (
            f"*Attack:* {unit_info['attack']}\n"
            f"*Defense:* {unit_info['defense']}\n"
            f"*Speed:* {unit_info['speed']}\n"
        )
        
        # Format cost
        cost_text = (
            f"*Cost:* 💰 {unit_info['cost']} Credits, "
            f"🪨 {unit_info['minerals']} Minerals, "
            f"⚡ {unit_info['energy']} Energy\n"
        )
        
        # Format training time
        training_time = unit_info["training_time"]
        minutes, seconds = divmod(training_time, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            training_time_text = f"*Training Time:* {hours}h {minutes}m\n"
        else:
            training_time_text = f"*Training Time:* {minutes}m {seconds}s\n"
        
        # Combine all sections
        unit_text = (
            f"*{name}*\n\n"
            f"{description}\n\n"
            f"{cost_text}"
            f"{training_time_text}"
            f"{stats_text}"
            f"{requirements_text}"
        )
        
        return unit_text
    
    except Exception as e:
        logging.error(f"Error formatting unit info: {e}", exc_info=True)
        return f"Error retrieving unit information for {unit_id}."

async def format_research_info(tech_id: str) -> str:
    """
    Format technology information for display.
    
    Args:
        tech_id: The technology ID
    
    Returns:
        Formatted technology information
    """
    try:
        tech_info = await get_research_info(tech_id)
        
        name = escape_markdown(tech_info["name"], version=2)
        description = escape_markdown(tech_info["description"], version=2)
        
        # Format requirements
        requirements_text = ""
        if tech_info["requirements"]:
            req_names = []
            for req_id in tech_info["requirements"]:
                req_info = await get_building_info(req_id)
                req_names.append(escape_markdown(req_info["name"], version=2))
            
            requirements_text = f"*Requires:* {', '.join(req_names)}\n"
        
        # Format effects
        effects_text = ""
        if "effects" in tech_info and tech_info["effects"]:
            effects = []
            for key, value in tech_info["effects"].items():
                effects.append(f"{key.replace('_', ' ').title()}: {value}")
            
            effects_text = f"*Effects:* {', '.join(effects)}\n"
        
        # Format cost
        cost_text = (
            f"*Cost:* 💰 {tech_info['cost']} Credits, "
            f"🪨 {tech_info['minerals']} Minerals, "
            f"⚡ {tech_info['energy']} Energy\n"
        )
        
        # Format research time
        research_time = tech_info["research_time"]
        minutes, seconds = divmod(research_time, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            research_time_text = f"*Research Time:* {hours}h {minutes}m\n"
        else:
            research_time_text = f"*Research Time:* {minutes}m {seconds}s\n"
        
        # Combine all sections
        tech_text = (
            f"*{name}*\n\n"
            f"{description}\n\n"
            f"{cost_text}"
            f"{research_time_text}"
            f"{requirements_text}"
            f"{effects_text}"
        )
        
        return tech_text
    
    except Exception as e:
        logging.error(f"Error formatting research info: {e}", exc_info=True)
        return f"Error retrieving technology information for {tech_id}."

async def format_battle_result(result: Dict[str, Any]) -> str:
    """
    Format battle results for display.
    
    Args:
        result: Dictionary with battle results
    
    Returns:
        Formatted battle results
    """
    try:
        # Get battle details
        battle_details = result.get("battle_details", {})
        result_type = result.get("result", "unknown")
        resources_gained = result.get("resources_gained", {})
        
        # Format attacker and defender info
        attacker_power = battle_details.get("attacker", {}).get("power", 0)
        attacker_roll = battle_details.get("attacker", {}).get("roll", 0)
        attacker_score = battle_details.get("attacker", {}).get("score", 0)
        
        defender_power = battle_details.get("defender", {}).get("power", 0)
        defender_roll = battle_details.get("defender", {}).get("roll", 0)
        defender_score = battle_details.get("defender", {}).get("score", 0)
        
        # Format result section
        if result_type == "win":
            result_text = "🏆 *Victory\\!*"
            
            # Format resources gained
            resources_text = (
                f"*Resources Gained:*\n"
                f"💰 {resources_gained.get('credits', 0)} Credits\n"
                f"🪨 {resources_gained.get('minerals', 0)} Minerals\n"
                f"⚡ {resources_gained.get('energy', 0)} Energy\n"
            )
        elif result_type == "loss":
            result_text = "❌ *Defeat\\!*"
            resources_text = "*No resources gained\\.*\n"
        else:  # Draw
            result_text = "🔄 *Draw\\!*"
            resources_text = "*No resources gained\\.*\n"
        
        # Format battle statistics
        battle_stats = (
            f"*Battle Statistics:*\n"
            f"Your Power: {attacker_power} \\(Roll: {attacker_roll:.2f}\\)\n"
            f"Enemy Power: {defender_power} \\(Roll: {defender_roll:.2f}\\)\n"
            f"Your Score: {attacker_score:.2f}\n"
            f"Enemy Score: {defender_score:.2f}\n"
        )
        
        # Combine all sections
        battle_text = (
            f"{result_text}\n\n"
            f"{battle_stats}\n"
            f"{resources_text}"
        )
        
        return battle_text
    
    except Exception as e:
        logging.error(f"Error formatting battle result: {e}", exc_info=True)
        return "Error formatting battle results."

async def format_scan_results(targets: List[Dict[str, Any]]) -> str:
    """
    Format scan results for display.
    
    Args:
        targets: List of target players with their details
    
    Returns:
        Formatted scan results
    """
    try:
        # Format header
        scan_text = "*Scan Results:*\n\n"
        
        # Format targets
        for i, target in enumerate(targets, 1):
            target_name = escape_markdown(target["name"], version=2)
            target_power = target["power"]
            
            scan_text += f"{i}\\. *{target_name}* \\- Power: {target_power}\n"
        
        scan_text += "\nSelect a target to attack\\."
        
        return scan_text
    
    except Exception as e:
        logging.error(f"Error formatting scan results: {e}", exc_info=True)
        return "Error formatting scan results."

async def format_alliance_info(alliance_info: Dict[str, Any]) -> str:
    """
    Format alliance information for display.
    
    Args:
        alliance_info: Dictionary with alliance information
    
    Returns:
        Formatted alliance information
    """
    try:
        # Escape text for Markdown V2
        alliance_name = escape_markdown(alliance_info["name"], version=2)
        leader_name = escape_markdown(alliance_info["leader_name"], version=2)
        join_code = escape_markdown(alliance_info["join_code"], version=2)
        
        # Format alliance stats
        alliance_stats = (
            f"👑 Leader: {leader_name}\n"
            f"👥 Members: {alliance_info['member_count']}\n"
            f"🏆 Power Ranking: {alliance_info['power_ranking']}\n"
        )
        
        # Format created date
        created_at = alliance_info.get("created_at", datetime.now())
        created_text = f"📅 Created: {created_at.strftime('%Y-%m-%d')}\n"
        
        # Format join code and role
        join_code_text = f"🔑 Join Code: `{join_code}`\n"
        role_text = f"🛡️ Your Role: {alliance_info['player_role'].capitalize()}\n"
        
        # Combine all sections
        alliance_text = (
            f"*Alliance: {alliance_name}*\n\n"
            f"{alliance_stats}\n"
            f"{created_text}"
            f"{join_code_text}"
            f"{role_text}"
        )
        
        return alliance_text
    
    except Exception as e:
        logging.error(f"Error formatting alliance info: {e}", exc_info=True)
        return "Error formatting alliance information."
