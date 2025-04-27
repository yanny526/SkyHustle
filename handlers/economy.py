from telegram import Update
from telegram.ext import ContextTypes
import json
import utils.db as db

# Load store and blackmarket items
def load_items():
    with open("data/items.json", "r") as f:
        data = json.load(f)
    return data

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Store items."""
    data = load_items()
    store_items = data["store_items"]

    text = "🛒 **SkyHustle Store** 🛒\n\n"
    for item in store_items:
        text += f"🛍️ {item['name']} — {item['price']} Gold\n"
    text += "\nBuy an item with `/buy <item_id>`!"

    await update.message.reply_text(text)

async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Black Market items."""
    data = load_items()
    black_items = data["blackmarket_items"]

    text = "🕵️ **Black Market** 🕵️\n\n"
    for item in black_items:
        text += f"🕶️ {item['name']} — {item['price']} Gold\n"
    text += "\nBuy a rare item with `/blackbuy <item_id>`!"

    await update.message.reply_text(text)
