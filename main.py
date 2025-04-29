# main.py

import os
import logging
import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
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
    building_system,
)
from utils.google_sheets import load_player_army, load_building_queue, get_building_level
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
        "Use the menu buttons below to navigate.",
        reply_markup=MENU_MARKUP
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔹 /tutorial — Guided setup\n"
        "🔹 /status   — Empire snapshot\n"
        "🔹 /lore     — Backstory\n\n"
        "Or tap the menu below:",
        reply_markup=MENU_MARKUP
    )

async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT, reply_markup=MENU_MARKUP)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = render_status_panel(str(update.effective_user.id))
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)

# ———————————————————————————————————————————————————————————————————————————
# Tutorial flows (highest priority)
# ———————————————————————————————————————————————————————————————————————————
for handler in [
    CommandHandler("tutorial",   tutorial_system.tutorial),
    CommandHandler("setname",    tutorial_system.setname),
    CommandHandler("ready",      tutorial_system.ready),
    CommandHandler("build",      tutorial_system.build),
    CommandHandler("mine",       tutorial_system.tutorial_mine),
    CommandHandler("minestatus", tutorial_system.tutorial_mine_status),
    CommandHandler("claimmine",  tutorial_system.tutorial_claim_mine),
    CommandHandler("train",      tutorial_system.tutorial_train),
    CommandHandler("trainstatus",tutorial_system.tutorial_trainstatus),
    CommandHandler("claimtrain", tutorial_system.tutorial_claim_train),
]:
    pass  # will add below in main()

# ———————————————————————————————————————————————————————————————————————————
# Menu button router
# ———————————————————————————————————————————————————————————————————————————
async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    pid = str(update.effective_user.id)

    if text == "🏗 Buildings":
        # list each building with its current level
        bld_q = load_building_queue(pid)
        lines = []
        for key in building_system.BUILDINGS:
            lvl = get_building_level(pid, key)
            # if it's upgrading, show "(upgrading)"
            suffix = " (upgrading)" if any(t['building_name']==key for t in bld_q.values()) else ""
            lines.append(f"• {key.title()}: Lv {lvl}{suffix}")
        msg = "<b>🏗 Buildings</b>\n" + "\n".join(lines) + "\n\n" \
              "Use /buildinfo [name] for details or /build [name] to upgrade."
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)

    elif text == "🛡️ Army":
        army = load_player_army(pid)
        if not army:
            msg = "🛡️ Your army is empty.\nUse /train [unit] [amt] to recruit."
        else:
            parts = [f"• {unit.title()}: {qty}" for unit, qty in army.items()]
            msg = "<b>🛡️ Army</b>\n" + "\n".join(parts) + "\n\n" \
                  "Use /army for full stats."
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)

    elif text == "⚙️ Status":
        panel = render_status_panel(pid)
        await update.message.reply_text(panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)

    elif text == "📜 Missions":
        await update.message.reply_text(
            "Use /missions to view and claim today's missions.",
            reply_markup=MENU_MARKUP
        )

    elif text == "🛒 Shop":
        await update.message.reply_text(
            "Use /shop to browse the normal shop\n"
            "Or /unlockblackmarket to unlock the Black Market.",
            reply_markup=MENU_MARKUP
        )

    elif text == "⚔️ Battle":
        await update.message.reply_text(
            "Use /attack [player_id] to strike\n"
            "Use /battle_status to see your battles\n"
            "Use /spy [player_id] to recon.",
            reply_markup=MENU_MARKUP
        )

    # anything else just falls through to regular command handlers

# ———————————————————————————————————————————————————————————————————————————
# Main setup
# ———————————————————————————————————————————————————————————————————————————
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tutorial handlers
    for h in [
        CommandHandler("tutorial",   tutorial_system.tutorial),
        CommandHandler("setname",    tutorial_system.setname),
        CommandHandler("ready",      tutorial_system.ready),
        CommandHandler("build",      tutorial_system.build),
        CommandHandler("mine",       tutorial_system.tutorial_mine),
        CommandHandler("minestatus", tutorial_system.tutorial_mine_status),
        CommandHandler("claimmine",  tutorial_system.tutorial_claim_mine),
        CommandHandler("train",      tutorial_system.tutorial_train),
        CommandHandler("trainstatus",tutorial_system.tutorial_trainstatus),
        CommandHandler("claimtrain", tutorial_system.tutorial_claim_train),
    ]:
        app.add_handler(h)

    # Core commands
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("lore",    lore))
    app.add_handler(CommandHandler("status",  status))

    # Menu router for button presses
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_router))

    # Fallback to existing systems
    app.add_handler(CommandHandler("build",      building_system.build))
    app.add_handler(CommandHandler("buildinfo",  building_system.buildinfo))
    app.add_handler(CommandHandler("buildstatus",building_system.buildstatus))

    app.add_handler(CommandHandler("mine",       timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus", timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine",  timer_system.claim_mining))

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

    # Unknown slash
    async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❓ I don’t recognize that. Try the menu below.", reply_markup=MENU_MARKUP)
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Global error handler
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
