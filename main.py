
import os
import asyncio
from telegram.ext import Application
from core_handlers import get_conversation_handler

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(get_conversation_handler())
    print("✅ SkyHustle bot is live...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
