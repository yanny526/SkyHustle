# main.py
import os
from telegram.ext import ApplicationBuilder
from modules.sheets_helper import initialize_sheets
from modules.registration import setup_registration
from modules.base_ui import setup_base_ui

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❗ BOT_TOKEN is not set. Please export it and retry.")
        return

    # 1) Initialize Sheets (must exist before any handler uses it)
    try:
        initialize_sheets()
        print("✅ Google Sheets initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Sheets: {e}")
        return

    # 2) Build the Telegram application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 3) Register handlers (we'll add more as we progress)
    setup_registration(app)
    setup_base_ui(app)  # Register the /base command handler

    # 4) Start polling
    print("🚀 SkyHustle Bot is starting…")
    app.run_polling()

if __name__ == "__main__":
    main() 