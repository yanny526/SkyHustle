# handlers/build.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from modules.buildings import Building
from utils.format import section_header

buildings_data = {
    "barracks": Building("Barracks", production_rate=10),
    "factory": Building("Factory", production_rate=15),
    "research_lab": Building("Research Lab", production_rate=20)
}

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    if not args:
        kb = [[InlineKeyboardButton(f"Build {building.name} (Level {building.level})", callback_data=f"build_{name}")] for name, building in buildings_data.items()]
        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('CONSTRUCTION MENU', '🏗️', 'blue')}\n\n"
            "Select a building to construct or upgrade:\n\n" +
            "\n".join([f"{name}: Level {building.level} - Production: {building.production_rate}/min" for name, building in buildings_data.items()]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    building_name = args[0].lower()
    if building_name in buildings_data:
        building = buildings_data[building_name]
        building.upgrade()
        await update.message.reply_text(
            f"🏗️ *Building Upgraded* 🏗️\n\n"
            f"{building.name} upgraded to Level {building.level}!\n"
            f"New Production Rate: {building.production_rate}/min",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Invalid building name. Use /build to see available buildings.",
            parse_mode="Markdown"
        )