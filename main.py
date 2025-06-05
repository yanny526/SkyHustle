import os
from telegram.ext import ApplicationBuilder
from modules.sheets_helper import initialize_sheets
from modules.registration import setup_registration

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❗ BOT_TOKEN is not set. Please export BOT_TOKEN before running.")
        return

    # 1. Initialize Google Sheets:
    try:
        initialize_sheets()
        print("✅ Google Sheets initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Sheets: {e}")
        return

    # 2. Build Telegram application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 3. Register handlers (start/registration, etc.)
    setup_registration(app)

    # 4. Run the bot
    print("🚀 SkyHustle Bot is starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
