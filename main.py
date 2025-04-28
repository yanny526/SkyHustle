# main.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# -------------- BOT TOKEN (Replace with your own token) --------------
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# -------------- /start command --------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ SkyHustle System Online!\n\nType /help to see available commands."
    )

# -------------- /help command --------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛡️ SkyHustle Help Menu\n\n"
        "Available Commands:\n"
        "- /status — View your Empire Status\n"
        "- /army — View Your Army\n"
        "- /mine — Start Mining\n"
        "- /train — Train Your Troops\n"
        "- /attack — Attack an Enemy\n"
        "- /missions — View Daily Missions\n"
        "- /shop — Open Normal Store\n"
        "- /blackmarket — Open Elite Store\n\n"
        "More features unlocking soon!"
    )
    await update.message.reply_text(help_text)

# -------------- Catch-all for unknown /commands --------------
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Unknown command. Type /help to see the list of available commands.")

# -------------- Main Setup --------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Unknown commands
    app.add_handler(CommandHandler(None, unknown_command))

    app.run_polling()

if __name__ == "__main__":
    main()
