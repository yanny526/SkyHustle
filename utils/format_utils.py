# utils/format_utils.py

BUILDING_EMOJI = {
    'Mine': '⛏️',
    'Power Plant': '⚡',
    'Barracks': '🛡️',
    'Workshop': '🔧',
}

UNIT_EMOJI = {
    'infantry': '👨‍✈️',
    'tanks': '🛡️',
    'artillery': '🚀',
}

def get_building_emoji(name: str) -> str:
    """
    Return the emoji for a given building name.
    """
    return BUILDING_EMOJI.get(name, '')

def get_unit_emoji(unit: str) -> str:
    """
    Return the emoji for a given unit type.
    """
    return UNIT_EMOJI.get(unit.lower(), '')

def bold(text: str) -> str:
    """
    Wrap text in Markdown bold.
    """
    return f"*{text}*"

def code(text: str) -> str:
    """
    Wrap text in Markdown inline code.
    """
    return f"`{text}`"
