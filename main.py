import os
from dotenv import load_dotenv
from telegram.ext import Application

from registration import setup_registration

# Load environment variables
load_dotenv()

async def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Set up registration handlers
    setup_registration(application)

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
