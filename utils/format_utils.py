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
    return BUILDING_EMOJI.get(name, '')

def get_unit_emoji(unit: str) -> str:
    return UNIT_EMOJI.get(unit.lower(), '')

def bold(text: str) -> str:
    return f"*{text}*"

def code(text: str) -> str:
    return f"`{text}`"

def section_header(title: str, emoji: str = "", underline: str = "═", color: str = "gold") -> str:
    """
    Create a visually appealing section header with optional emoji and color.
    """
    return f"\n[{color}]╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗[/]\n" \
           f" [{color}]║ [{emoji}]  {title}  [{emoji}] ║[/]\n" \
           f" [{color}]╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝[/]\n"

def format_bar(current: int, maximum: int, length: int = 10) -> str:
    ratio = (current / maximum) if maximum else 0
    filled = int(ratio * length)
    empty = length - filled
    bar = '█' * filled + '░' * empty
    percent = int(ratio * 100)
    return f"[{bar}] {percent}%"

def get_build_time(building: str, level: int) -> int:
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
    if building == 'Mine':
        return (100, 50 * level, 10 * level)
    elif building == 'Power Plant':
        return (100, 30 * level, 8 * level)
    elif building == 'Barracks':
        return (150, 70 * level, 12 * level)
    elif building == 'Workshop':
        return (200, 100 * level, 15 * level)
    return (0, 0, 0)
