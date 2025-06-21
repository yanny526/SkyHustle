# handlers.py (Final Diagnostic: /start & DB Test)

import logging
import google_sheets # We need this to test the connection

logger = logging.getLogger(__name__)

def register_handlers(bot, scheduler):
    """A targeted handler to test the /start command and the initial database call."""
    
    @bot.message_handler(commands=['start'])
    def start_diagnostic_handler(message):
        user_id = message.from_user.id
        logger.info(f"DIAGNOSTIC: /start received from {user_id}.")
        bot.reply_to(message, "✅ Step 1/2: /start command received by handler.")
        
        try:
            logger.info(f"DIAGNOSTIC: Attempting to find player data for {user_id}...")
            _, player_data = google_sheets.find_player_row(user_id)
            
            if player_data:
                logger.info(f"DIAGNOSTIC: Found existing player data.")
                bot.reply_to(message, "✅ Step 2/2: SUCCESS! Found your existing commander data in the database.")
            else:
                logger.info(f"DIAGNOSTIC: No existing player data found.")
                bot.reply_to(message, "✅ Step 2/2: SUCCESS! You are a new commander (no data found in database).")

        except Exception as e:
            logger.critical(f"DIAGNOSTIC: FAILURE during Google Sheets lookup: {e}")
            bot.reply_to(message, f"❌ Step 2/2: FAILED! A critical error occurred while contacting the database: {e}")

    @bot.message_handler(func=lambda message: True)
    def catch_all_handler(message):
        """Catch any other messages during this test."""
        logger.info(f"DIAGNOSTIC: Received non-start message: {message.text}")
        bot.reply_to(message, "This is the diagnostic bot. Please send /start to test the primary function.")