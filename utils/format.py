# utils/format.py

def section_header(title: str, emoji: str, color: str) -> str:
    """
    Create a visually appealing section header with emoji and color.
    """
    return f"\n[{color}]═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗[/]\n" \
           f" [{emoji}]  {title}  [{emoji}] ║[/]\n" \
           f"[{color}]═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝[/]\n"