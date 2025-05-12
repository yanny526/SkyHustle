"""
Validator utilities for SkyHustle.
Functions for validating input data.
"""
import re
from config import MAX_NAME_LENGTH

def validate_name(name):
    """
    Validate a player or alliance name.
    
    Args:
        name: Name to validate
        
    Returns:
        str: "valid" if valid, otherwise an error message
    """
    if not name or not name.strip():
        return "Name cannot be empty"
    
    if len(name) > MAX_NAME_LENGTH:
        return f"Name must be {MAX_NAME_LENGTH} characters or less"
    
    # Check for disallowed characters
    if not re.match(r'^[a-zA-Z0-9 \-_]+$', name):
        return "Name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return "valid"

def validate_join_code(code):
    """
    Validate an alliance join code.
    
    Args:
        code: Join code to validate
        
    Returns:
        str: "valid" if valid, otherwise an error message
    """
    if not code or not code.strip():
        return "Join code cannot be empty"
    
    if len(code) != 6:
        return "Join code must be exactly 6 characters"
    
    if not re.match(r'^[A-Z0-9]+$', code):
        return "Join code can only contain uppercase letters and numbers"
    
    return "valid"

def validate_resource_amount(amount):
    """
    Validate a resource amount.
    
    Args:
        amount: Amount to validate
        
    Returns:
        str: "valid" if valid, otherwise an error message
    """
    try:
        amount = int(amount)
        if amount <= 0:
            return "Amount must be greater than 0"
        
        if amount > 1000000:
            return "Amount must be 1,000,000 or less"
        
        return "valid"
    except (ValueError, TypeError):
        return "Amount must be a valid number"