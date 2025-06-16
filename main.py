"""
Main entry point for SkyHustle Telegram bot.
"""
import os
import asyncio
from telegram.ext import ApplicationBuilder
from handlers.base_handler import registration_handler

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("🔑 BOT_TOKEN is not set in environment")
    app = ApplicationBuilder().token(token).build()

    # Player registration
    app.add_handler(registration_handler())

    # TODO: add other handlers (/base, /build, etc.) once ready

    print("🚀 SkyHustle Bot is starting...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main()) 