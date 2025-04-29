import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
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

# ——— Logging & Error Handler —————————————————————————————————————————
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception:")
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Oops, something went wrong. Please try again later."
        )

# ——— BOT TOKEN ————————————————————————————————————————————————————————
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

# ——— Backstory & Simple Commands —————————————————————————————————————
LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions...\n"
    "Welcome to SKYHUSTLE."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\n"
        "Type /tutorial or /menu to begin."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔹 /tutorial — Guided setup\n"
        "🔹 /menu     — Open game menu\n"
        "🔹 /status   — Empire snapshot\n"
        "🔹 /lore     — Backstory"
    )

async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = render_status_panel(str(update.effective_user.id))
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML)

# ——— In-Chat Menu ————————————————————————————————————————————————————
MENU_KEY = "skyhustle_menu"

def build_menu():
    keyboard = [
        [InlineKeyboardButton("🏗 Buildings", callback_data=f"{MENU_KEY}:buildings")],
        [InlineKeyboardButton("🛡️ Army", callback_data=f"{MENU_KEY}:army")],
        [InlineKeyboardButton("⚙️ Status", callback_data=f"{MENU_KEY}:status")],
        [InlineKeyboardButton("📜 Missions", callback_data=f"{MENU_KEY}:missions")],
        [InlineKeyboardButton("🛒 Shop", callback_data=f"{MENU_KEY}:shop")],
        [InlineKeyboardButton("⚔️ Battle", callback_data=f"{MENU_KEY}:battle")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Select a section:", reply_markup=build_menu())

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    section = query.data.split(":", 1)[1]
    pid = str(query.from_user.id)

    if section == "buildings":
        text = building_system.menu_buildings(pid)
    elif section == "army":
        text = army_system.menu_army(pid)
    elif section == "status":
        text = render_status_panel(pid)
    elif section == "missions":
        text = mission_system.menu_missions(pid)
    elif section == "shop":
        text = shop_system.menu_shop(pid)
    elif section == "battle":
        text = battle_system.menu_battle(pid)
    else:
        text = "Unknown section."

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_menu()
    )

# ——— Catch unknown slash commands —————————————————————————————————————
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Unknown command—try /menu")

# ——— Main & Handler Registration ——————————————————————————————————————
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tutorial flow (intercepts build/mine/train during tutorial)
    app.add_handler(CommandHandler("tutorial", tutorial_system.tutorial))
    app.add_handler(CommandHandler("setname", tutorial_system.setname))
    app.add_handler(CommandHandler("ready", tutorial_system.ready))
    app.add_handler(CommandHandler("build", tutorial_system.build))
    app.add_handler(CommandHandler("mine", tutorial_system.tutorial_mine))
    app.add_handler(CommandHandler("minestatus", tutorial_system.tutorial_mine_status))
    app.add_handler(CommandHandler("claimmine", tutorial_system.tutorial_claim_mine))
    app.add_handler(CommandHandler("train", tutorial_system.tutorial_train))
    app.add_handler(CommandHandler("trainstatus", tutorial_system.tutorial_trainstatus))
    app.add_handler(CommandHandler("claimtrain", tutorial_system.tutorial_claim_train))

    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lore", lore))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("menu", menu))

    # Menu callbacks
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=f"^{MENU_KEY}:"))

    # Fallback: real systems once tutorial is past interception
    app.add_handler(CommandHandler("build", building_system.build))
    app.add_handler(CommandHandler("buildinfo", building_system.buildinfo))
    app.add_handler(CommandHandler("buildstatus", building_system.buildstatus))

    app.add_handler(CommandHandler("mine", timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus", timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine", timer_system.claim_mining))

    app.add_handler(CommandHandler("train", army_system.train_units))
    app.add_handler(CommandHandler("army", army_system.view_army))
    app.add_handler(CommandHandler("trainstatus", army_system.training_status))
    app.add_handler(CommandHandler("claimtrain", army_system.claim_training))

    app.add_handler(CommandHandler("missions", mission_system.missions))
    app.add_handler(CommandHandler("storymissions", mission_system.storymissions))
    app.add_handler(CommandHandler("epicmissions", mission_system.epicmissions))
    app.add_handler(CommandHandler("claimmission", mission_system.claimmission))

    app.add_handler(CommandHandler("attack", battle_system.attack))
    app.add_handler(CommandHandler("battle_status", battle_system.battle_status))
    app.add_handler(CommandHandler("spy", battle_system.spy))

    app.add_handler(CommandHandler("shop", shop_system.shop))
    app.add_handler(CommandHandler("buy", shop_system.buy))
    app.add_handler(CommandHandler("unlockblackmarket", shop_system.unlock_blackmarket))
    app.add_handler(CommandHandler("blackmarket", shop_system.blackmarket))
    app.add_handler(CommandHandler("bmbuy", shop_system.bmbuy))

    # Unknown command fallback
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Global error handler
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
