# bot/handlers/__init__.py
"""bot.handlers subpackage."""

from .start  import handler as start_handler
from .attack import handler as attack_handler
from .build  import handler as build_handler
from .train  import handler as train_handler

__all__ = [
    "start_handler",
    "attack_handler",
    "build_handler",
    "train_handler",
]
