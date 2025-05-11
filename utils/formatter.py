"""
Formatter utilities for SkyHustle.
Functions for formatting messages, escape markdown, and create visually appealing responses.
"""
import logging
import re

logger = logging.getLogger(__name__)

def escape_markdown(text):
    """
    Escape Markdown V2 special characters.
    
    Args:
        text: Text to escape
        
    Returns:
        str: Escaped text
    """
    if not text:
        return ""
    
    # Characters that need to be escaped in Markdown V2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape backslash first to avoid double escaping
    text = text.replace('\\', '\\\\')
    
    # Escape all other special characters
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_error(message):
    """
    Format an error message.
    
    Args:
        message: Error message
        
    Returns:
        str: Formatted error message
    """
    return f"❌ {message}"

def format_success(message):
    """
    Format a success message.
    
    Args:
        message: Success message
        
    Returns:
        str: Formatted success message
    """
    return f"✅ {message}"

def format_info(message):
    """
    Format an info message.
    
    Args:
        message: Info message
        
    Returns:
        str: Formatted info message
    """
    return f"ℹ️ {message}"

def format_status_message(player):
    """
    Format player status message.
    
    Args:
        player: Player data dictionary
        
    Returns:
        str: Formatted status message
    """
    try:
        # Escape player name for Markdown V2
        player_name = escape_markdown(player.get('display_name', 'Commander'))
        
        # Get resources
        credits = player.get('credits', 0)
        minerals = player.get('minerals', 0)
        energy = player.get('energy', 0)
        skybucks = player.get('skybucks', 0)
        
        # Format resource bars (each bar is 10 units)
        max_resources = max(credits, minerals, energy, 1)  # Avoid division by zero
        credit_bar = format_resource_bar(credits, max_resources)
        mineral_bar = format_resource_bar(minerals, max_resources)
        energy_bar = format_resource_bar(energy, max_resources)
        
        # Format message
        message = (
            f"*{player_name}'s Status*\n\n"
            f"💰 *Credits:* {credits} {credit_bar}\n"
            f"🔷 *Minerals:* {minerals} {mineral_bar}\n"
            f"⚡ *Energy:* {energy} {energy_bar}\n"
            f"💎 *SkyBucks:* {skybucks}\n\n"
        )
        
        # Add buildings section if data is available
        from modules.building import get_player_buildings
        buildings = get_player_buildings(player.get('player_id'))
        
        if buildings:
            message += "*Buildings:*\n"
            for building in buildings[:5]:  # Show up to 5 buildings
                if building.get('status') == 'queued':
                    message += f"🏗️ {escape_markdown(building.get('building_name', 'Building'))} \\- Constructing\n"
                else:
                    message += f"🏢 {escape_markdown(building.get('building_name', 'Building'))} \\- Level {building.get('level', 1)}\n"
            
            if len(buildings) > 5:
                message += f"\\.\\.\\. and {len(buildings) - 5} more\n\n"
            else:
                message += "\n"
        else:
            message += "*Buildings:* None yet\\. Use /build to construct\\.\n\n"
        
        # Add units section if data is available
        from modules.unit import get_player_units
        units = get_player_units(player.get('player_id'))
        
        if units:
            message += "*Units:*\n"
            for unit in units[:5]:  # Show up to 5 unit types
                count = unit.get('count', 1)
                if unit.get('status') == 'training':
                    message += f"🔄 {escape_markdown(unit.get('unit_name', 'Unit'))} x{count} \\- Training\n"
                else:
                    message += f"👥 {escape_markdown(unit.get('unit_name', 'Unit'))} x{count}\n"
            
            if len(units) > 5:
                message += f"\\.\\.\\. and {len(units) - 5} more\n\n"
            else:
                message += "\n"
        else:
            message += "*Units:* None yet\\. Use /train to recruit\\.\n\n"
        
        # Add alliance info if player is in an alliance
        if 'alliance_id' in player and player['alliance_id']:
            from modules.alliance import get_alliance
            alliance = get_alliance(player['alliance_id'])
            if alliance:
                message += (
                    f"*Alliance:* {escape_markdown(alliance.get('alliance_name', 'Unknown'))}\n"
                    f"*Role:* {escape_markdown(player.get('alliance_role', 'Member'))}\n"
                )
        
        return message
    except Exception as e:
        logger.error(f"Error formatting status message: {e}")
        return "Error generating status. Please try again later."

def format_resource_bar(value, max_value, length=10):
    """
    Format a resource bar using emoji blocks.
    
    Args:
        value: Current resource value
        max_value: Maximum value for scaling
        length: Length of the bar in characters
        
    Returns:
        str: Formatted resource bar
    """
    if max_value <= 0:
        return ""
    
    filled = min(length, int((value / max_value) * length))
    
    if filled <= 0:
        return "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️"
    
    return "▪️" * filled + "▫️" * (length - filled)

def format_building_info(building):
    """
    Format building information.
    
    Args:
        building: Building type data
        
    Returns:
        str: Formatted building info
    """
    name = escape_markdown(building.get('name', 'Building'))
    description = escape_markdown(building.get('description', 'No description available.'))
    
    credits = building.get('cost_credits', 0)
    minerals = building.get('cost_minerals', 0)
    energy = building.get('cost_energy', 0)
    
    build_time = building.get('build_time', 60)
    build_time_str = format_time(build_time)
    
    message = (
        f"*{name}*\n\n"
        f"{description}\n\n"
        f"*Costs:*\n"
        f"💰 Credits: {credits}\n"
        f"🔷 Minerals: {minerals}\n"
        f"⚡ Energy: {energy}\n\n"
        f"*Build Time:* {build_time_str}\n\n"
    )
    
    if 'produces' in building:
        produces = building.get('produces', {})
        message += (
            f"*Produces:*\n"
            f"💰 Credits: {produces.get('credits', 0)}/hour\n"
            f"🔷 Minerals: {produces.get('minerals', 0)}/hour\n"
            f"⚡ Energy: {produces.get('energy', 0)}/hour\n\n"
        )
    
    return message

def format_alliance_info(alliance):
    """
    Format alliance information.
    
    Args:
        alliance: Alliance data
        
    Returns:
        str: Formatted alliance info
    """
    name = escape_markdown(alliance.get('alliance_name', 'Alliance'))
    member_count = alliance.get('member_count', 0)
    total_power = alliance.get('total_power', 0)
    
    message = (
        f"*{name}*\n\n"
        f"*Members:* {member_count}/{escape_markdown(str(15))}\n"
        f"*Alliance Power:* {total_power}\n\n"
    )
    
    if 'join_code' in alliance:
        join_code = escape_markdown(alliance.get('join_code', ''))
        message += f"*Join Code:* `{join_code}`\n\n"
    
    return message

def format_player_info(player):
    """
    Format player information for display.
    
    Args:
        player: Player data
        
    Returns:
        str: Formatted player info
    """
    name = escape_markdown(player.get('display_name', 'Commander'))
    
    message = (
        f"*{name}*\n\n"
        f"*Power:* {player.get('power', 0)}\n"
        f"*Experience:* {player.get('experience', 0)}\n\n"
    )
    
    if 'alliance_id' in player and player['alliance_id']:
        from modules.alliance import get_alliance
        alliance = get_alliance(player['alliance_id'])
        if alliance:
            alliance_name = escape_markdown(alliance.get('alliance_name', 'Unknown'))
            message += f"*Alliance:* {alliance_name}\n"
    
    return message

def format_time(seconds):
    """
    Format seconds into a human-readable time string.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''}"
