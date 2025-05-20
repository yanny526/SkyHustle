"""
Rate limiting utilities for SkyHustle 2
"""

import time
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# Store cooldowns for each user and command
cooldowns = {}

def rate_limit(seconds: int):
    """
    Decorator to rate limit commands
    Args:
        seconds: Cooldown time in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            command = func.__name__
            
            # Create key for this user and command
            key = f"{user_id}:{command}"
            
            # Check if user is on cooldown
            if key in cooldowns:
                remaining = cooldowns[key] - time.time()
                if remaining > 0:
                    await update.message.reply_text(
                        f"Please wait {int(remaining)} seconds before using this command again."
                    )
                    return
            
            # Set cooldown
            cooldowns[key] = time.time() + seconds
            
            # Execute command
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def clear_cooldown(user_id: int, command: str = None):
    """
    Clear cooldown for a user and command
    Args:
        user_id: User ID
        command: Command name (optional, clears all commands if None)
    """
    if command:
        key = f"{user_id}:{command}"
        cooldowns.pop(key, None)
    else:
        # Clear all cooldowns for this user
        keys_to_remove = [k for k in cooldowns.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            cooldowns.pop(key, None) 