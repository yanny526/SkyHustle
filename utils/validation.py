# utils/validation.py

import re

def is_valid_name(name):
    """Check if the name is valid: only letters, numbers, and spaces are allowed."""
    pattern = re.compile(r"^[A-Za-z0-9 ]+$")
    return bool(pattern.match(name))
