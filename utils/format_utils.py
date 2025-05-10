def section_header(title: str, emoji: str, color: str = None) -> str:
    """Simple Telegram-friendly section header."""
    return f"{emoji} *{title}* {emoji}\n"
