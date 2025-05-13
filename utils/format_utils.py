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
    return BUILDING_EMOJI.get(name, '')

def get_unit_emoji(unit: str) -> str:
    return UNIT_EMOJI.get(unit.lower(), '')

def bold(text: str) -> str:
    return f"*{text}*"

def code(text: str) -> str:
    return f"`{text}`"

def format_bar(current: int, maximum: int, length: int = 10) -> str:
    ratio = (current / maximum) if maximum else 0
    filled = int(ratio * length)
    empty = length - filled
    bar = '█' * filled + '░' * empty
    percent = int(ratio * 100)
    return f"[{bar}] {percent}%"

def get_build_time(building: str, level: int) -> int:
    """
    Return upgrade duration in seconds for the given building at target level.
    """
    if building == 'Mine':
        return 30 * 60 * level
    elif building == 'Power Plant':
        return 20 * 60 * level
    elif building == 'Barracks':
        return 45 * 60 * level
    elif building == 'Workshop':
        return 60 * 60 * level
    return 0

def get_build_costs(building: str, level: int) -> tuple[int, int, int]:
    """
    Return (credits, minerals, energy) cost for upgrading a building to the specified level.
    """
    if building == 'Mine':
        return (100, 50 * level, 10 * level)
    elif building == 'Power Plant':
        return (100, 30 * level, 8 * level)
    elif building == 'Barracks':
        return (150, 70 * level, 12 * level)
    elif building == 'Workshop':
        return (200, 100 * level, 15 * level)
    return (0, 0, 0)

def section_header(title: str, pad_char: str = '-', pad_count: int = 5) -> str:
    """
    Render a section header, e.g. '----- Title -----'
    """
    return f"{pad_char * pad_count} {title} {pad_char * pad_count}"
