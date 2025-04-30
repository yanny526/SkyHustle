# core_handlers.py (Part 1 of X)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram import Update

from mission_system import handle_missions
from building_system import handle_build
from training_system import handle_training
from combat_system import handle_attack
from spy_system import handle_spy
from status_panel_system import handle_status
from tech_tree_system import handle_research
from blackmarket_system import handle_blackmarket
from reward_system import handle_rewards
from store_system import handle_store
from base_expansion_system import handle_expand
from zone_control_system import handle_zone
from utils.ui_helpers import send_main_menu

# ── Start Command ────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update, context)

# ── Handler Registration ─────────────────────────────────────────────────
def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("missions", handle_missions))
    app.add_handler(CommandHandler("build", handle_build))
    app.add_handler(CommandHandler("train", handle_training))
    app.add_handler(CommandHandler("attack", handle_attack))
    app.add_handler(CommandHandler("spy", handle_spy))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("research", handle_research))
    app.add_handler(CommandHandler("blackmarket", handle_blackmarket))
    app.add_handler(CommandHandler("rewards", handle_rewards))
    app.add_handler(CommandHandler("store", handle_store))
    app.add_handler(CommandHandler("expand", handle_expand))
    app.add_handler(CommandHandler("zone", handle_zone))
# core_handlers.py (Part 2 of X)

from mission_system import button_missions
from building_system import button_build
from training_system import button_training
from combat_system import button_combat
from spy_system import button_spy
from tech_tree_system import button_research
from blackmarket_system import button_blackmarket
from reward_system import button_rewards
from store_system import button_store
from base_expansion_system import button_expand
from zone_control_system import button_zone

# ── Button Callback Handler ──────────────────────────────────────────────
def register_callback_handlers(app):
    app.add_handler(CallbackQueryHandler(button_missions, pattern="^mission_"))
    app.add_handler(CallbackQueryHandler(button_build, pattern="^build_"))
    app.add_handler(CallbackQueryHandler(button_training, pattern="^train_"))
    app.add_handler(CallbackQueryHandler(button_combat, pattern="^combat_"))
    app.add_handler(CallbackQueryHandler(button_spy, pattern="^spy_"))
    app.add_handler(CallbackQueryHandler(button_research, pattern="^tech_"))
    app.add_handler(CallbackQueryHandler(button_blackmarket, pattern="^bm_"))
    app.add_handler(CallbackQueryHandler(button_rewards, pattern="^reward_"))
    app.add_handler(CallbackQueryHandler(button_store, pattern="^store_"))
    app.add_handler(CallbackQueryHandler(button_expand, pattern="^expand_"))
    app.add_handler(CallbackQueryHandler(button_zone, pattern="^zone_"))

# ── Unknown Fallback ─────────────────────────────────────────────────────
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Unknown command. Try /start to begin.")

def register_fallback(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
# core_handlers.py (Part 3 of 3)

import os
from telegram.ext import Application

def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise Exception("BOT_TOKEN not found in environment variables")

    app = Application.builder().token(token).build()

    # Register all handlers
    register_handlers(app)
    register_callback_handlers(app)
    register_fallback(app)

    # Start polling
    print("🚀 SkyHustle Bot is now running...")
    app.run_polling()
