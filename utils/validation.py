import re

def is_valid_name(name):
    """Validate player name: no emojis, no special characters, and reasonable length."""
    # Block emojis
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U000024C2-\U0001F251"  # Enclosed characters
        "]+", flags=re.UNICODE
    )

    # Block special characters: ! @ # % ^ & ? (and a few others)
    special_chars_pattern = re.compile(r"[!@#%^&*()?<>:{}[\]|\/=~`\"']")

    if emoji_pattern.search(name):
        return False
    if special_chars_pattern.search(name):
        return False
    if not (3 <= len(name) <= 20):
        return False
    return True
