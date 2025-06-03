import os
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from handlers.start_handler import get_start_handler

# Optionally, load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE64_CREDS = os.getenv('BASE64_CREDS')
SHEET_ID = os.getenv('SHEET_ID')

if not TOKEN or not BASE64_CREDS or not SHEET_ID:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN, BASE64_CREDS, or SHEET_ID environment variable.")

async def base_command(update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder for /base command
    await update.message.reply_text("🏠 Welcome to your base! (Base UI coming soon)")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    # Add /start ConversationHandler
    application.add_handler(get_start_handler())
    # Add /base placeholder
    application.add_handler(CommandHandler('base', base_command))
    print("SkyHustle bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()