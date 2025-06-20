# handlers.py (Diagnostic Echo Test Version)

import logging
logger = logging.getLogger(__name__)

def register_handlers(bot, scheduler):
    """A simple handler that replies to any message with the same text."""
    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        logger.info(f"ECHO TEST: Received message from {message.from_user.id}. Replying...")
        bot.reply_to(message, f"Echo: {message.text}")