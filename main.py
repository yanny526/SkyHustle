# main.py

import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
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
    building_system
)
from utils import google_sheets
from utils.ui_helpers import render_status_panel

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions...\n"
    "Welcome to SKYHUSTLE."
)

# --- Inline Menus ---
MAIN_MENU_PAGE1 = InlineKeyboardMarkup([
    [ InlineKeyboardButton("🛰️ Status", callback_data="menu_status"),
      InlineKeyboardButton("🛡️ Army",   callback_data="menu_army") ],
    [ InlineKeyboardButton("⛏️ Mine",   switch_inline_query_current_chat="/mine "),
      InlineKeyboardButton("🏭 Train",  switch_inline_query_current_chat="/train ") ],
    [ InlineKeyboardButton("▶️ Next",   callback_data="menu_page2") ],
])

MAIN_MENU_PAGE2 = InlineKeyboardMarkup([
    [ InlineKeyboardButton("🏗️ Build",  switch_inline_query_current_chat="/build ") ,
      InlineKeyboardButton("🛒 Shop",   switch_inline_query_current_chat="/shop ") ],
    [ InlineKeyboardButton("📜 Missions", switch_inline_query_current_chat="/missions"),
      InlineKeyboardButton("📖 Lore",    callback_data="menu_lore") ],
    [ InlineKeyboardButton("◀️ Back",    callback_data="menu_page1") ],
])

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /menu — show page 1 of the main menu """
    await update.message.reply_text(
        "📋 *Main Menu*\nChoose an action:",
        reply_markup=MAIN_MENU_PAGE1,
        parse_mode=ParseMode.MARKDOWN,
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handle inline‐button presses """
    query = update.callback_query
    await query.answer()  # remove “loading” spinner

    data = query.data
    user_id = str(query.from_user.id)

    if data == "menu_page2":
        await query.edit_message_text(
            "📋 *Main Menu — Page 2*",
            reply_markup=MAIN_MENU_PAGE2,
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "menu_page1":
        await query.edit_message_text(
            "📋 *Main Menu — Page 1*",
            reply_markup=MAIN_MENU_PAGE1,
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "menu_status":
        # send a fresh status panel
        panel = render_status_panel(user_id)
        await query.message.reply_text(panel, parse_mode=ParseMode.HTML)
    elif data == "menu_army":
        # call your existing army view
        # note: we create a fake Update with the same chat/message context
        fake_update = Update(
            update.update_id,
            message=query.message
        )
        await army_system.view_army(fake_update, context)
    elif data == "menu_lore":
        await query.message.reply_text(LORE_TEXT)

# --- Bot Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\n\n"
        "Type /tutorial or /menu to get started."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Help • SkyHustle\n\n"
        "/menu   — Open the in-chat menu\n"
        "/tutorial — First-time walkthrough\n"
        "/status — Show full status panel\n"
        "/army   — View your army\n"
        "/lore   — Read the backstory"
    )

async def lore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Unknown command. Type /help or /menu.")

# --- Main setup ---

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tutorial flow (high priority)
    app.add_handler(CommandHandler("tutorial",    tutorial_system.tutorial))
    app.add_handler(CommandHandler("setname",     tutorial_system.setname))
    app.add_handler(CommandHandler("ready",       tutorial_system.ready))
    app.add_handler(CommandHandler("build",       tutorial_system.build))
    app.add_handler(CommandHandler("mine",        tutorial_system.tutorial_mine))
    app.add_handler(CommandHandler("minestatus",  tutorial_system.tutorial_mine_status))
    app.add_handler(CommandHandler("claimmine",   tutorial_system.tutorial_claim_mine))
    app.add_handler(CommandHandler("train",       tutorial_system.tutorial_train))
    app.add_handler(CommandHandler("trainstatus", tutorial_system.tutorial_trainstatus))
    app.add_handler(CommandHandler("claimtrain",  tutorial_system.tutorial_claim_train))

    # Core commands
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_command))
    app.add_handler(CommandHandler("lore",    lore_command))
    app.add_handler(CommandHandler("status",  status_command))
    app.add_handler(CommandHandler("menu",    menu_command))

    # Fallback handlers
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(CommandHandler("mine",       timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus", timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine",  timer_system.claim_mining))

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

    app.add_handler(CommandHandler("buildstatus",  building_system.buildstatus))
    app.add_handler(CommandHandler("buildinfo",    building_system.buildinfo))

    # Catch-all
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    app.run_polling()

if __name__ == "__main__":
    main()
