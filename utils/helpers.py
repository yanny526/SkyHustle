"""
Helper functions for the SkyHustle Telegram bot.
Provides utility functions for various tasks.
"""
import json
import logging
import asyncio
import base64
import random
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

def encode_callback_data(callback_type: str, data: Dict[str, Any]) -> str:
    """
    Encode callback data for inline keyboard buttons.
    
    Args:
        callback_type: Type of callback
        data: Data to include in the callback
    
    Returns:
        Encoded string for callback_data
    """
    try:
        # Create callback data dictionary
        callback_data = {
            "type": callback_type,
            "data": data
        }
        
        # Convert to JSON string
        json_data = json.dumps(callback_data)
        
        # Ensure the data isn't too long for Telegram
        if len(json_data) > 64:
            # If too long, use a simpler format
            simplified_data = {
                "t": callback_type,
                "d": data
            }
            json_data = json.dumps(simplified_data)
            
            # If still too long, truncate
            if len(json_data) > 64:
                logging.warning(f"Callback data too long, truncating: {json_data}")
                json_data = json_data[:60] + "..."
        
        return json_data
    
    except Exception as e:
        logging.error(f"Error encoding callback data: {e}", exc_info=True)
        # Return a safe fallback
        return json.dumps({"type": "error", "data": {}})

def decode_callback_data(callback_data: str) -> Tuple[str, Dict[str, Any]]:
    """
    Decode callback data from inline keyboard buttons.
    
    Args:
        callback_data: The encoded callback data
    
    Returns:
        Tuple of (callback_type, data)
    """
    try:
        # Parse JSON data
        parsed_data = json.loads(callback_data)
        
        # Handle different formats
        if "type" in parsed_data:
            callback_type = parsed_data["type"]
            data = parsed_data.get("data", {})
        elif "t" in parsed_data:
            # Handle simplified format
            callback_type = parsed_data["t"]
            data = parsed_data.get("d", {})
        else:
            # Unknown format
            callback_type = "unknown"
            data = {}
        
        return callback_type, data
    
    except Exception as e:
        logging.error(f"Error decoding callback data: {e}", exc_info=True)
        # Return safe fallback
        return "error", {}

def create_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard from button definitions.
    
    Args:
        buttons: List of button rows, each containing button definitions
    
    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []
    
    for row in buttons:
        keyboard_row = []
        for button in row:
            text = button["text"]
            callback_data = button.get("callback_data")
            url = button.get("url")
            
            if callback_data:
                keyboard_row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
            elif url:
                keyboard_row.append(InlineKeyboardButton(text=text, url=url))
        
        if keyboard_row:
            keyboard.append(keyboard_row)
    
    return InlineKeyboardMarkup(keyboard)

def get_command_args(context: ContextTypes.DEFAULT_TYPE) -> List[str]:
    """
    Extract command arguments from a message.
    
    Args:
        context: The context object containing the message and arguments
    
    Returns:
        List of command arguments
    """
    if not context.args:
        return []
    
    return context.args

def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID string.
    
    Args:
        prefix: Optional prefix for the ID
    
    Returns:
        Unique ID string
    """
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Add some randomness
    random_part = ''.join(random.choices('0123456789ABCDEF', k=6))
    
    # Combine parts
    unique_id = f"{prefix}{timestamp}{random_part}"
    
    return unique_id

def parse_time_string(time_str: str) -> Optional[int]:
    """
    Parse a time string into seconds.
    
    Args:
        time_str: Time string in format like "1h", "30m", "2h30m", etc.
    
    Returns:
        Seconds, or None if invalid format
    """
    try:
        # Check if just a number (assume seconds)
        if time_str.isdigit():
            return int(time_str)
        
        total_seconds = 0
        current_num = ""
        
        for char in time_str:
            if char.isdigit():
                current_num += char
            elif char == 'h' and current_num:
                total_seconds += int(current_num) * 3600
                current_num = ""
            elif char == 'm' and current_num:
                total_seconds += int(current_num) * 60
                current_num = ""
            elif char == 's' and current_num:
                total_seconds += int(current_num)
                current_num = ""
            else:
                # Invalid character
                return None
        
        # If there are leftover digits without a unit, assume seconds
        if current_num:
            total_seconds += int(current_num)
        
        return total_seconds
    
    except Exception:
        return None

def format_time_from_seconds(seconds: int) -> str:
    """
    Format seconds into a human-readable time string.
    
    Args:
        seconds: Number of seconds
    
    Returns:
        Formatted time string (e.g., "2h 30m")
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or (hours > 0 and seconds > 0):
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into chunks of size n.
    
    Args:
        lst: The list to split
        n: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def get_resource_emoji(resource_type: str) -> str:
    """
    Get the emoji for a resource type.
    
    Args:
        resource_type: Type of resource
    
    Returns:
        Emoji string
    """
    emojis = {
        "credits": "💰",
        "minerals": "🪨",
        "energy": "⚡",
        "skybucks": "💎",
        "experience": "🌟",
        "attack": "⚔️",
        "defense": "🛡️",
        "speed": "🏃",
        "health": "❤️",
        "power": "💪"
    }
    
    return emojis.get(resource_type.lower(), "")

def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """
    Create a progress bar using emojis.
    
    Args:
        current: Current value
        maximum: Maximum value
        length: Length of the progress bar
    
    Returns:
        Progress bar string
    """
    if maximum <= 0:
        filled = length
    else:
        filled = int((current / maximum) * length)
    
    # Ensure filled doesn't exceed length
    filled = min(filled, length)
    
    # Create progress bar
    bar = "▓" * filled + "░" * (length - filled)
    
    return bar

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: User input text
    
    Returns:
        Sanitized text
    """
    # Remove potentially problematic characters
    # This is a simple implementation - production code might use more sophisticated validation
    unsafe_chars = ['<', '>', '&', '"', "'", '\\', '/', ';', '`']
    for char in unsafe_chars:
        text = text.replace(char, '')
    
    return text.strip()
