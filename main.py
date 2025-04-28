# main.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from systems import timer_system, army_system  # Import both systems
from utils import google_sheets  # Needed to initialize Google Sheets connection

# -------------- BOT TOKEN (Replace with your real token) --------------
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# -------------- Backstory Text --------------
LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions.\n"
    "The planet's surface is dead. Survivors now live aboard colossal flying fortresses known as SkyHustles.\n\n"
    "🛡️ As Commander, you lead your SkyHustle to survival.\n"
    "Mine rare resources, build your forces, and conquer the skies.\n\n"
    "🕶️ Rumors speak of a forbidden Black Market — where power can be bought, but destiny must still be earned.\n\n"
    "⚔️ Fight bravely, Commander.\n"
    "The skies belong to the strong. Welcome to SKYHUSTLE."
)

# -------------- /start command (Short cinematic intro) --------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\n\n"
        "The skies are yours to conquer.\n"
        "Type /help to begin your journey."
    )

# -------------- /help command --------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛡️ SkyHustle Help Menu\n\n"
        "Available Commands:\n"
        "- /status — View your Empire Status (coming soon)\n"
        "- /army — View Your Army\n"
        "- /train [unit] [amount] — Train New Units\n"
        "- /mine [resource] [amount] — Start Mining\n"
        "- /minestatus — View Mining Progress\n"
        "- /claimmine — Claim Completed Mining\n"
        "- /attack — Attack an Enemy (coming soon)\n"
        "- /missions — View Daily Missions (coming soon)\n"
        "- /shop — Open Normal Store (coming soon)\n"
        "- /blackmarket — Open Elite Store (coming soon)\n"
        "- /lore — Read the SkyHustle Backstory"
    )
    await update.message.reply_text(help_text)

# -------------- /lore command --------------
async def lore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT)

# -------------- Catch unknown commands --------------
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Unknown command. Type /help to see available commands.")

# -------------- Main Setup --------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Core Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lore", lore_command))

    # Timer System Commands
    app.add_handler(CommandHandler("mine", timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus", timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine", timer_system.claim_mining))

    # Army System Commands
    app.add_handler(CommandHandler("train", army_system.train_units))
    app.add_handler(CommandHandler("army", army_system.view_army))
    app.add_handler(CommandHandler("trainstatus", army_system.training_status))  # New Command
    app.add_handler(CommandHandler("claimtrain", army_system.claim_training))    # New Command

    # Catch unknown /commands
    app.add_handler(CommandHandler(None, unknown_command))

    app.run_polling()

if __name__ == "__main__":
    main()
