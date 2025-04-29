# main.py

import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from systems import (
    tutorial_system,
    timer_system,
    army_system,
    battle_system,
    mission_system,
    shop_system,
    building_system
)
from utils import google_sheets
from utils.ui_helpers import render_status_panel  # unified HTML panel

# -------------- BOT TOKEN (from env var) --------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

# -------------- Backstory Text --------------
LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions.\n"
    "The planet's surface is dead. Survivors now live aboard colossal flying fortresses known as SkyHustles.\n\n"
    "🛡️ As Commander, you lead your SkyHustle to survival.\n"
    "Mine rare resources, build your forces, and conquer the skies.\n\n"
    "🕶️ Rumors speak of a forbidden Black Market — where power can be bought, but destiny must still be earned.\n\n"
    "⚔️ Fight bravely, Commander. The skies belong to the strong. Welcome to SKYHUSTLE."
)

# -------------- /start --------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\n\n"
        "Type /tutorial for a quick guided setup—or /help to see all commands."
    )

# -------------- /help --------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛡️ SkyHustle Help Menu\n\n"
        "- /tutorial — Guided first-time walkthrough\n"
        "- /status   — View full empire status\n"
        "- /army     — View your raw army listing\n"
        "- /train    — Enlist new units\n"
        "- /mine     — Start resource mining\n"
        "- /missions — Daily & story missions\n"
        "- /shop     — Trade at the market\n"
        "- /lore     — Read the backstory"
    )
    await update.message.reply_text(help_text)

# -------------- /lore --------------
async def lore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT)

# -------------- /status --------------
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status — Show your HTML-formatted empire snapshot.
    """
    player_id = str(update.effective_user.id)
    panel = render_status_panel(player_id)
    # send with HTML parse mode for styling
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML)

# -------------- Unknown commands fallback --------------
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Unknown command. Type /help to see available commands.")

# -------------- Main Setup & Handlers --------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tutorial flow (highest priority)
    app.add_handler(CommandHandler("tutorial",   tutorial_system.tutorial))
    app.add_handler(CommandHandler("setname",    tutorial_system.setname))
    app.add_handler(CommandHandler("ready",      tutorial_system.ready))
    app.add_handler(CommandHandler("build",      tutorial_system.build))
    app.add_handler(CommandHandler("mine",       tutorial_system.tutorial_mine))
    app.add_handler(CommandHandler("minestatus", tutorial_system.tutorial_mine_status))
    app.add_handler(CommandHandler("claimmine",  tutorial_system.tutorial_claim_mine))
    app.add_handler(CommandHandler("train",      tutorial_system.tutorial_train))
    app.add_handler(CommandHandler("trainstatus",tutorial_system.tutorial_trainstatus))
    app.add_handler(CommandHandler("claimtrain", tutorial_system.tutorial_claim_train))

    # Core commands
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_command))
    app.add_handler(CommandHandler("lore",    lore_command))
    app.add_handler(CommandHandler("status",  status_command))

    # Fallback timer & army & others
    app.add_handler(CommandHandler("mine",      timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus",timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine", timer_system.claim_mining))

    app.add_handler(CommandHandler("train",       army_system.train_units))
    app.add_handler(CommandHandler("army",        army_system.view_army))
    app.add_handler(CommandHandler("trainstatus", army_system.training_status))
    app.add_handler(CommandHandler("claimtrain",  army_system.claim_training))

    app.add_handler(CommandHandler("missions",      mission_system.missions))
    app.add_handler(CommandHandler("storymissions", mission_system.storymissions))
    app.add_handler(CommandHandler("epicmissions",  mission_system.epicmissions))
    app.add_handler(CommandHandler("claimmission",  mission_system.claimmission))

    app.add_handler(CommandHandler("attack",        battle_system.attack))
    app.add_handler(CommandHandler("battle_status", battle_system.battle_status))
    app.add_handler(CommandHandler("spy",           battle_system.spy))

    app.add_handler(CommandHandler("shop",              shop_system.shop))
    app.add_handler(CommandHandler("buy",               shop_system.buy))
    app.add_handler(CommandHandler("unlockblackmarket", shop_system.unlock_blackmarket))
    app.add_handler(CommandHandler("blackmarket",       shop_system.blackmarket))
    app.add_handler(CommandHandler("bmbuy",              shop_system.bmbuy))

        # --- Building System ---
    app.add_handler(CommandHandler("build",      building_system.build))
    app.add_handler(CommandHandler("buildinfo",  building_system.buildinfo))
    app.add_handler(CommandHandler("buildstatus",building_system.buildstatus))


    # Catch-all for unknown slash commands
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    app.run_polling()

if __name__ == "__main__":
    main()
