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
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy an item from the store."""
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("🛒 Usage: /buy <item_id>")

    item_id = context.args[0].lower()
    data = load_items()
    store_items = data["store_items"]

    selected_item = next((item for item in store_items if item["id"] == item_id), None)

    if not selected_item:
        return await update.message.reply_text("🛒 Item not found in store!")

    player = db.get_player_data(telegram_id)
    if player["Gold"] < selected_item["price"]:
        return await update.message.reply_text("💰 Not enough Gold!")

    # Deduct price
    db.update_player_resources(telegram_id, gold_delta=-selected_item["price"])

    # Apply item effect
    db.update_player_resources(
        telegram_id,
        gold_delta=selected_item.get("gold", 0),
        stone_delta=selected_item.get("stone", 0),
        iron_delta=selected_item.get("iron", 0),
        energy_delta=selected_item.get("energy", 0)
    )

    # Special: activate shield if bought
    if selected_item.get("shield"):
        db.player_profile.update_cell(db.find_player(telegram_id), 9, "Yes")

    await update.message.reply_text(f"✅ You bought {selected_item['name']}!")

async def blackbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy an item from the Black Market."""
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("🕵️ Usage: /blackbuy <item_id>")

    item_id = context.args[0].lower()
    data = load_items()
    black_items = data["blackmarket_items"]

    selected_item = next((item for item in black_items if item["id"] == item_id), None)

    if not selected_item:
        return await update.message.reply_text("🕵️ Item not found in Black Market!")

    player = db.get_player_data(telegram_id)
    if player["Gold"] < selected_item["price"]:
        return await update.message.reply_text("💰 Not enough Gold for Black Market purchase!")

    # Deduct price
    db.update_player_resources(telegram_id, gold_delta=-selected_item["price"])

    # 🔥 Future: add item to player's inventory (right now just confirm purchase)
    await update.message.reply_text(f"🕵️ You secretly purchased {selected_item['name']}! Shhh... 🤫")
async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Use a purchased item (simple version)."""
    telegram_id = update.effective_user.id

    if len(context.args) != 1:
        return await update.message.reply_text("🎯 Usage: /use <item_id>")

    item_id = context.args[0].lower()

    if item_id == "basicshield":
        player = db.get_player_data(telegram_id)
        if player["ShieldActive"] == "Yes":
            return await update.message.reply_text("🛡️ You already have a shield active!")

        db.player_profile.update_cell(db.find_player(telegram_id), 9, "Yes")
        await update.message.reply_text("🛡️ Basic Shield activated! You're protected for 24 hours.")

    elif item_id == "revivekit":
        await update.message.reply_text("🛠️ Revive Kit used! (Troop revive feature coming soon...)")

    elif item_id == "infinityscout":
        await update.message.reply_text("🛰️ Infinity Scout launched! (Spying system coming soon...)")

    elif item_id == "hazmatdrone":
        await update.message.reply_text("☣️ Hazmat Drone deployed! (Radiation zones coming soon...)")

    elif item_id == "empdevice":
        await update.message.reply_text("🔌 EMP Device activated! (Enemy shields disruption coming soon...)")

    else:
        await update.message.reply_text("❓ Unknown item or feature not available yet!")
