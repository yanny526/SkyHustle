import os
from telegram.ext import Application
from core_handlers import get_conversation_handler

BOT_TOKEN = os.environ.get("BOT_TOKEN")

application = Application.builder().token(BOT_TOKEN).build()

# Register handlers
application.add_handler(get_conversation_handler())

print("✅ SkyHustle bot is live...")
application.run_polling()
