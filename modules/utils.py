from telegram.helpers import escape_markdown

def escape_markdown_v2(text: str) -> str:
    """Escape text for Telegram's MarkdownV2 format."""
    return escape_markdown(text, version=2) 