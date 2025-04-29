# main.py

import os
import logging
import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
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
    building_system,
)
from utils.ui_helpers import render_status_panel

# ———————————————————————————————————————————————————————————————————————————
# Logging
# ———————————————————————————————————————————————————————————————————————————
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception:")
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(
            "❌ Oops, something went wrong. Please try again later."
        )

# ———————————————————————————————————————————————————————————————————————————
# Persistent Reply Keyboard
# ———————————————————————————————————————————————————————————————————————————
MAIN_MENU = [
    [KeyboardButton("🏗 Buildings"), KeyboardButton("🛡️ Army")],
    [KeyboardButton("⚙️ Status"),    KeyboardButton("📜 Missions")],
    [KeyboardButton("🛒 Shop"),      KeyboardButton("⚔️ Battle")],
]
MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

# ———————————————————————————————————————————————————————————————————————————
# Bot Token
# ———————————————————————————————————————————————————————————————————————————
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")

# ———————————————————————————————————————————————————————————————————————————
# /start, /help, /lore, /status
# ———————————————————————————————————————————————————————————————————————————
LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions...\n"
    "Welcome to SKYHUSTLE."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\n\n"
        "Use the buttons below to navigate the SkyHustle UI.",
        reply_markup=MENU_MARKUP
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔹 /tutorial — Guided setup\n"
        "🔹 /status   — Empire snapshot\n"
        "🔹 /lore     — Backstory\n\n"
        "Or just tap the buttons below:",
        reply_markup=MENU_MARKUP
    )

async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT, reply_markup=MENU_MARKUP)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = render_status_panel(str(update.effective_user.id))
    await update.message.reply_text(panel, parse_mode="HTML", reply_markup=MENU_MARKUP)

# ———————————————————————————————————————————————————————————————————————————
# /tutorial and tutorial flows
# ———————————————————————————————————————————————————————————————————————————
app_tutorial = [
    CommandHandler("tutorial", tutorial_system.tutorial),
    CommandHandler("setname",  tutorial_system.setname),
    CommandHandler("ready",    tutorial_system.ready),
    CommandHandler("build",    tutorial_system.build),
    CommandHandler("mine",     tutorial_system.tutorial_mine),
    CommandHandler("minestatus", tutorial_system.tutorial_mine_status),
    CommandHandler("claimmine", tutorial_system.tutorial_claim_mine),
    CommandHandler("train",    tutorial_system.tutorial_train),
    CommandHandler("trainstatus", tutorial_system.tutorial_trainstatus),
    CommandHandler("claimtrain",  tutorial_system.tutorial_claim_train),
]

# ———————————————————————————————————————————————————————————————————————————
# Fallback menu‐button handler
# ———————————————————————————————————————————————————————————————————————————
async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    pid = str(update.effective_user.id)

    if text == "🏗 Buildings":
        # builds up a pretty HTML list of all buildings
        html = building_system.menu_buildings(pid)
        await update.message.reply_text(html, parse_mode="HTML", reply_markup=MENU_MARKUP)

    elif text == "🛡️ Army":
        html = army_system.menu_army(pid)
        await update.message.reply_text(html, parse_mode="HTML", reply_markup=MENU_MARKUP)

    elif text == "⚙️ Status":
        html = render_status_panel(pid)
        await update.message.reply_text(html, parse_mode="HTML", reply_markup=MENU_MARKUP)

    elif text == "📜 Missions":
        html = mission_system.menu_missions(pid)
        await update.message.reply_text(html, parse_mode="HTML", reply_markup=MENU_MARKUP)

    elif text == "🛒 Shop":
        html = shop_system.menu_shop(pid)
        await update.message.reply_text(html, parse_mode="HTML", reply_markup=MENU_MARKUP)

    elif text == "⚔️ Battle":
        html = battle_system.menu_battle(pid)
        await update.message.reply_text(html, parse_mode="HTML", reply_markup=MENU_MARKUP)

    else:
        # pass through to real commands if they matched
        return

# ———————————————————————————————————————————————————————————————————————————
# Main setup
# ———————————————————————————————————————————————————————————————————————————
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # tutorial handlers (first)
    for h in app_tutorial:
        app.add_handler(h)

    # core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_cmd))
    app.add_handler(CommandHandler("lore",  lore))
    app.add_handler(CommandHandler("status",status))

    # button router for our menu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_router))

    # fallback to your existing systems
    app.add_handler(CommandHandler("build",     building_system.build))
    app.add_handler(CommandHandler("buildinfo", building_system.buildinfo))
    app.add_handler(CommandHandler("buildstatus",building_system.buildstatus))

    app.add_handler(CommandHandler("mine",      timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus",timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine", timer_system.claim_mining))

    app.add_handler(CommandHandler("train",      army_system.train_units))
    app.add_handler(CommandHandler("army",       army_system.view_army))
    app.add_handler(CommandHandler("trainstatus",army_system.training_status))
    app.add_handler(CommandHandler("claimtrain", army_system.claim_training))

    app.add_handler(CommandHandler("missions",      mission_system.missions))
    app.add_handler(CommandHandler("storymissions", mission_system.storymissions))
    app.add_handler(CommandHandler("epicmissions",  mission_system.epicmissions))
    app.add_handler(CommandHandler("claimmission",  mission_system.claimmission))

    app.add_handler(CommandHandler("attack",        battle_system.attack))
    app.add_handler(CommandHandler("battle_status", battle_system.battle_status))
    app.add_handler(CommandHandler("spy",           battle_system.spy))

    app.add_handler(CommandHandler("shop",               shop_system.shop))
    app.add_handler(CommandHandler("buy",                shop_system.buy))
    app.add_handler(CommandHandler("unlockblackmarket",  shop_system.unlock_blackmarket))
    app.add_handler(CommandHandler("blackmarket",        shop_system.blackmarket))
    app.add_handler(CommandHandler("bmbuy",               shop_system.bmbuy))

    # unknown‐command fallback
    async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❓ I don’t recognize that. Try the buttons below.", reply_markup=MENU_MARKUP)
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # global error handler
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
