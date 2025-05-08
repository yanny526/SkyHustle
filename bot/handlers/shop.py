# handlers/shop.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

items = [
    {"name": "Construction Accelerator", "price": 500, "description": "Finishes building upgrades instantly"},
    {"name": "Training Boost", "price": 300, "description": "Reduces unit training time by 50% for 1 hour"},
    {"name": "Energy Surge", "price": 200, "description": "Restores 100 energy points"}
]

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"Buy {item['name']} ({item['price']} credits)", callback_data=f"buy_{i}")] for i, item in enumerate(items)]
    kb.append([InlineKeyboardButton("Close", callback_data="close")])

    await update.message.reply_text(
        "🛒 *Normal Shop* 🛒\n\n"
        "Use resources to purchase helpful items:\n\n" +
        "\n".join([f"{i+1}. {item['name']}: {item['price']}💰 - {item['description']}" for i, item in enumerate(items)]),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
