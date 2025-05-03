# utils/time_utils.py

def format_hhmmss(seconds: int) -> str:
    """
    Convert a number of seconds into an HH:MM:SS string.
    """
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"
