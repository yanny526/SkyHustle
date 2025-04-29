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
from systems.building_system import BUILDINGS
from utils.ui_helpers import render_status_panel

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions...\n"
    "Welcome to SKYHUSTLE."
)

# ——— Inline Menus ———
MENU_PAGE1 = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🛰️ Status", callback_data="menu_status"),
        InlineKeyboardButton("🛡️ Army",   callback_data="menu_army"),
    ],
    [
        InlineKeyboardButton("⛏️ Mine",   switch_inline_query_current_chat="/mine "),
        InlineKeyboardButton("🏭 Train",  switch_inline_query_current_chat="/train "),
    ],
    [ InlineKeyboardButton("▶️ Next", callback_data="menu_page2") ],
])

MENU_PAGE2 = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🏗️ Buildings", callback_data="menu_buildings"),
        InlineKeyboardButton("🔧 Upgrade",  switch_inline_query_current_chat="/build "),
    ],
    [
        InlineKeyboardButton("🛒 Shop",      switch_inline_query_current_chat="/shop "),
        InlineKeyboardButton("📜 Missions", switch_inline_query_current_chat="/missions "),
    ],
    [ InlineKeyboardButton("◀️ Back", callback_data="menu_page1") ],
])

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show page 1 of the main menu."""
    await update.message.reply_text(
        "📋 *Main Menu – Page 1*\nChoose an action:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MENU_PAGE1
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline‐button presses from our /menu."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)

    # Page navigation
    if data == "menu_page2":
        await query.edit_message_text(
            "📋 *Main Menu – Page 2*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=MENU_PAGE2
        )
        return
    if data == "menu_page1":
        await query.edit_message_text(
            "📋 *Main Menu – Page 1*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=MENU_PAGE1
        )
        return

    # Status & Army
    if data == "menu_status":
        panel = render_status_panel(user_id)
        await query.message.reply_text(panel, parse_mode=ParseMode.HTML)
        return

    if data == "menu_army":
        # reuse your army_system.view_army
        fake_update = Update(update.update_id, message=query.message)
        await army_system.view_army(fake_update, context)
        return

    # Lore
    if data == "menu_lore":
        await query.message.reply_text(LORE_TEXT)
        return

    # Buildings list
    if data == "menu_buildings":
        buttons = [
            [InlineKeyboardButton(b.replace("_"," ").title(), callback_data=f"building_{b}")]
            for b in BUILDINGS.keys()
        ]
        buttons.append([InlineKeyboardButton("◀️ Back", callback_data="menu_page2")])
        kb = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "🏗️ *Buildings*\nSelect one to view details:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
        return

    # Single‐building detail
    if data.startswith("building_"):
        key = data.split("_",1)[1]
        lvl = google_sheets.get_building_level(user_id, key)
        nxt = lvl + 1
        cost = BUILDINGS[key]["resource_cost"](nxt)
        eff  = BUILDINGS[key]["effect"](nxt) or {}
        cost_str = " | ".join(f"{k.title()}: {v}" for k,v in cost.items())
        eff_str  = ", ".join(f"{k.replace('_',' ').title()} +{v}" for k,v in eff.items()) or "(no immediate effect)"

        text = (
            f"🏗️ *{key.replace('_',' ').title()}*\n"
            f"• Current Level: *{lvl}*\n"
            f"• Next Level:   *{nxt}*\n"
            f"• Cost:         {cost_str}\n"
            f"• Effect:       {eff_str}\n\n"
            + render_status_panel(user_id)
        )
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

# ——— Bot Command Handlers ———
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\nType /tutorial or /menu to begin."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Help – SkyHustle*\n\n"
        "/menu     — Open in-chat menu\n"
        "/tutorial — Guided first-time walkthrough\n"
        "/status   — Full empire snapshot\n"
        "/army     — View your army\n"
        "/lore     — Read the backstory",
        parse_mode=ParseMode.MARKDOWN
    )

async def lore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Unknown command. Type /help or /menu.")

# ——— Main ———
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tutorial flow (highest priority)
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

    # CallbackQuery for inline menus
    app.add_handler(CallbackQueryHandler(menu_callback))

    # Fallback for everything else
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

    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.run_polling()

if __name__ == "__main__":
    main()
