# Bot
# bot.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# -------------- BOT TOKEN (Replace with your own token) --------------
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# -------------- /start command --------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ SkyHustle System Online!\n\nType ,help to see available commands."
    )

# -------------- ,help command --------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛡️ SkyHustle Help Menu\n\n"
        "Available Commands:\n"
        "- ,status — View your Empire Status\n"
        "- ,army — View Your Army\n"
        "- ,mine — Start Mining\n"
        "- ,attack — Attack an Enemy\n"
        "- ,missions — View Daily Missions\n"
        "- ,shop — Open Normal Store\n"
        "- ,blackmarket — Open Elite Store\n\n"
        "More features unlocking soon!"
    )
    await update.message.reply_text(help_text)

# -------------- Catch-all for other text messages --------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text.startswith(","):
        await update.message.reply_text("🚀 Command recognized, feature coming soon!")
    else:
        await update.message.reply_text("🤖 Unknown input. Type ,help to see commands.")

# -------------- Main setup --------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^,help$'), help_command))

    app.run_polling()

if __name__ == "__main__":
    main()
