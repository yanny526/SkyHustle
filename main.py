import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# System imports
from systems import (
    tutorial_system,
    timer_system,
    army_system,
    battle_system,
    mission_system,
    shop_system,
    blackmarket_system,
    spy_system,
    building_system,
    expansion_system,
    rewards_system,
    training_system,
    tech_tree_system,
    zone_control_system,
    trading_system,
)

from utils.google_sheets import (
    load_player_army,
    load_resources,
    load_building_queue
)
from utils.ui_helpers import render_status_panel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")

MAIN_MENU = [
    [KeyboardButton("🏗️ Buildings"), KeyboardButton("🛡️ Army")],
    [KeyboardButton("📦 Inventory"), KeyboardButton("📜 Missions")],
    [KeyboardButton("🛒 Shop"), KeyboardButton("⚔️ Battle")],
    [KeyboardButton("🛰️ Spy"), KeyboardButton("🧪 Research")],
    [KeyboardButton("🗺️ Zones"), KeyboardButton("💱 Trade")],
    [KeyboardButton("⚙️ Status"), KeyboardButton("🎁 Rewards")],
]

MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander! Use the menu below to navigate.",
        reply_markup=MENU_MARKUP
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "SkyHustle Commands:\n"
        "• /start — Initialize\n"
        "• /status — View your empire\n"
        "• /tutorial — Quick walkthrough\n"
        "Or use the Telegram menu buttons.",
        reply_markup=MENU_MARKUP
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception:")
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("❌ Something went wrong.")
def register_handlers(app: ApplicationBuilder):
    app.add_error_handler(error_handler)

    # Core Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))

    # Tutorial
    app.add_handler(CommandHandler("tutorial", tutorial_system.tutorial))
    app.add_handler(CommandHandler("setname", tutorial_system.setname))
    app.add_handler(CommandHandler("ready", tutorial_system.ready))

    # Buildings
    app.add_handler(CommandHandler("build", building_system.build))
    app.add_handler(CommandHandler("buildstatus", building_system.buildstatus))
    app.add_handler(CommandHandler("buildinfo", building_system.buildinfo))

    # Army & Training
    app.add_handler(CommandHandler("train", training_system.train_units))
    app.add_handler(CommandHandler("trainstatus", training_system.training_status))
    app.add_handler(CommandHandler("claimtrain", training_system.claim_training))
    app.add_handler(CommandHandler("army", army_system.view_army))

    # Battle
    app.add_handler(CommandHandler("attack", battle_system.attack))
    app.add_handler(CommandHandler("battle_status", battle_system.battle_status))
    app.add_handler(CommandHandler("spy", battle_system.spy))

    # Missions
    app.add_handler(CommandHandler("missions", mission_system.view_missions))
    app.add_handler(CommandHandler("claimmission", mission_system.claim_mission))

    # Shop & Black Market
    app.add_handler(CommandHandler("shop", shop_system.shop))
    app.add_handler(CommandHandler("buy", shop_system.buy))
    app.add_handler(CommandHandler("blackmarket", blackmarket_system.blackmarket))
    app.add_handler(CommandHandler("bmbuy", blackmarket_system.bmbuy))

    # Spy System
    app.add_handler(CommandHandler("scout", spy_system.scout))
    app.add_handler(CommandHandler("reports", spy_system.reports))

    # Research / Tech Tree
    app.add_handler(CommandHandler("tech", tech_tree_system.tech_tree))
    app.add_handler(CommandHandler("research", tech_tree_system.research_tech))

    # Base Expansion
    app.add_handler(CommandHandler("expand", expansion_system.expand_base))
    app.add_handler(CommandHandler("zoneinfo", expansion_system.zone_info))

    # Rewards
    app.add_handler(CommandHandler("daily", rewards_system.claim_daily_reward))

    # Zone Control
    app.add_handler(CommandHandler("zones", zone_control_system.zones))
    app.add_handler(CommandHandler("claimzone", zone_control_system.claim_zone))

    # Trading
    app.add_handler(CommandHandler("trade", trading_system.trade))
    app.add_handler(CommandHandler("market", trading_system.market))

    # Fallback
    app.add_handler(MessageHandler(filters.COMMAND, lambda u, c: u.message.reply_text(
        "Unknown command. Use /help or the menu.", reply_markup=MENU_MARKUP
    )))

    # Menu Buttons
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("⚙️ Status"), status))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📜 Missions"), mission_system.view_missions))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🎁 Rewards"), rewards_system.claim_daily_reward))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🏗️ Buildings"), building_system.buildstatus))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛡️ Army"), army_system.view_army))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛒 Shop"), shop_system.shop))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("⚔️ Battle"), battle_system.attack))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛰️ Spy"), spy_system.reports))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🧪 Research"), tech_tree_system.tech_tree))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🗺️ Zones"), zone_control_system.zones))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("💱 Trade"), trading_system.market))


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_handlers(app)
    app.run_polling()
