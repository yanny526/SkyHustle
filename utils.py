"""
utils.py:

This file contains utility functions used across the SkyHustle Telegram bot application.
"""

import re
import gspread
from config import SHEET_ID

def validate_user_input(input_text: str, expected_type: type) -> bool:
    """
    Validates user input to ensure it matches the expected data type.

    Args:
        input_text: The text input from the user.
        expected_type: The expected data type (e.g., int, float, str).

    Returns:
        True if the input matches the expected type, False otherwise.
    """
    try:
        if expected_type == int:
            int(input_text)
            return True
        elif expected_type == float:
            float(input_text)
            return True
        elif expected_type == str:
            return isinstance(input_text, str)
        else:
            return False  # Unsupported type
    except ValueError:
        return False

def format_number(number: int) -> str:
    """
    Formats a number with commas for better readability (e.g., 1000000 -> 1,000,000).

    Args:
        number: The number to format.

    Returns:
        The formatted number as a string.
    """
    return f"{number:,}"

def extract_number(text: str) -> int or None:
    """
    Extracts the first integer from a string.

    Args:
        text: The string to extract the number from.

    Returns:
        The first integer found in the string, or None if no integer is found.
    """
    if not text:
        return None

    match = re.search(r'\d+', text)
    if match:
        return int(match.group(0))
    else:
        return None

def is_valid_coordinates(x: int, y: int, grid_size: int = 100) -> bool:
    """
    Checks if the given coordinates are within the valid grid boundaries.
    Defaults to a 100x100 grid.

    Args:
        x: The x-coordinate.
        y: The y-coordinate.
        grid_size: The size of the grid (default: 100).

    Returns:
        True if the coordinates are valid, False otherwise.
    """
    return 1 <= x <= grid_size and 1 <= y <= grid_size

def sheet_exists(gc, sheet_name: str) -> bool:
    """
    Checks if a sheet with the given name exists in the Google Sheet.

    Args:
        gc: The gspread client object.
        sheet_name: The name of the sheet to check.

    Returns:
        True if the sheet exists, False otherwise.
    """
    try:
        gc.open_by_key(SHEET_ID).worksheet(sheet_name)
        return True
    except gspread.exceptions.WorksheetNotFound:
        return False
    except Exception as e:
        print(f"Error checking if sheet exists: {e}")
        return False # Return false on other errors to prevent crashing

# Example Usage (for testing - remove in final version)
if __name__ == '__main__':
    # Test validate_user_input
    print(f"validate_user_input('123', int): {validate_user_input('123', int)}")
    print(f"validate_user_input('123.45', float): {validate_user_input('123.45', float)}")
    print(f"validate_user_input('abc', str): {validate_user_input('abc', str)}")
    print(f"validate_user_input('abc', int): {validate_user_input('abc', int)}")

    # Test format_number
    print(f"format_number(1000000): {format_number(1000000)}")
    print(f"format_number(123456789): {format_number(123456789)}")

    # Test extract_number
    print(f"extract_number('abc123def'): {extract_number('abc123def')}")
    print(f"extract_number('abc'): {extract_number('abc')}")
    print(f"extract_number('123abc456'): {extract_number('123abc456')}")

    # Test is_valid_coordinates
    print(f"is_valid_coordinates(10, 20): {is_valid_coordinates(10, 20)}")
    print(f"is_valid_coordinates(0, 50): {is_valid_coordinates(0, 50)}")
    print(f"is_valid_coordinates(100, 100): {is_valid_coordinates(100, 100)}")
    print(f"is_valid_coordinates(101, 50): {is_valid_coordinates(101, 50)}")
