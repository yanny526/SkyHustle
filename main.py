import os
from dotenv import load_dotenv
from telegram.ext import Application

from registration import setup_registration

# Load environment variables
load_dotenv()

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    setup_registration(application)
    application.run_polling()

if __name__ == "__main__":
    main()
