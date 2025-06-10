# main.py
import os
from dotenv import load_dotenv
from telegram.ext import Application
from modules.sheets_helper import initialize_sheets
from modules.registration import setup_registration
from modules.base_ui import setup_base_ui
from modules.building_system import setup_building_system
from modules.training_system import setup_training_system

def main() -> None:
    # Load environment variables
    load_dotenv()
    
    # Initialize Google Sheets
    initialize_sheets()
    
    # Build the application
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Register handlers
    setup_registration(app)
    setup_base_ui(app)
    setup_building_system(app)
    setup_training_system(app)
    
    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main() 