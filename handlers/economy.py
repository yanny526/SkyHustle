# handlers/economy.py (FULLY FIXED)

from telegram import Update
from telegram.ext import ContextTypes
import json
import utils.db as db

# Load normal store items
def load_store_items():
    with open("data/items.json", "r") as f:
        data = json.load(f)
    return data["store_items"]

# Load blackmarket items
def load_blackmarket_items():
    with open("data/items.json", "r") as f:
        data = json.load(f)
    return data["blackmarket_items"]

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_items = load_store_items()
    text = "\U0001F6D2 **SkyHustle Store** \U0001F6D2\n\n"
    for item in store_items:
        text += f"ℹ️ {item['id']} | {item['name']} — {item['price']} Gold\n"
    text += "\n\U0001F6D2 To buy an item, type `/buy <item_id>`!"
    await update.message.reply_text(text)

async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blackmarket_items = load_blackmarket_items()
    text = "\U0001F575️‍♂️ **SkyHustle Black Market** \U0001F575️‍♂️\n\n"
    for item in blackmarket_items:
        text += f"ℹ️ {item['id']} | {item['name']} — {item['price']} Gold\n"
    text += "\n\U0001F6D2 To buy a black market item, type `/blackbuy <item_id>`!"
    await update.message.reply_text(text)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("\U0001F6D2 Usage: /buy <item_id>")

    item_id = context.args[0].lower()
    store_items = load_store_items()
    selected_item = next((item for item in store_items if item["id"].lower() == item_id), None)

    if not selected_item:
        return await update.message.reply_text("\U0001F6D2 Item not found in store!")

    player = db.get_player_data(telegram_id)
    if player["Gold"] < selected_item["price"]:
        return await update.message.reply_text("\ud83d\udcb0 Not enough Gold!")

    db.update_player_resources(telegram_id, gold_delta=-selected_item["price"])

    if selected_item.get("gold") or selected_item.get("stone") or selected_item.get("iron") or selected_item.get("energy"):
        db.update_player_resources(
            telegram_id,
            gold_delta=selected_item.get("gold", 0),
            stone_delta=selected_item.get("stone", 0),
            iron_delta=selected_item.get("iron", 0),
            energy_delta=selected_item.get("energy", 0)
        )
        await update.message.reply_text(f"✅ You bought {selected_item['name']}!")
    else:
        if not db.get_inventory(telegram_id):
            db.create_inventory(telegram_id)
        db.add_to_inventory(telegram_id, selected_item['id'])
        await update.message.reply_text(f"✅ {selected_item['name']} added to your inventory!")

async def blackbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("\U0001F575️ Usage: /blackbuy <item_id>")

    item_id = context.args[0].lower()
    black_items = load_blackmarket_items()
    selected_item = next((item for item in black_items if item["id"].lower() == item_id), None)

    if not selected_item:
        return await update.message.reply_text("\U0001F575️ Item not found in Black Market!")

    player = db.get_player_data(telegram_id)
    if player["Gold"] < selected_item["price"]:
        return await update.message.reply_text("\ud83d\udcb0 Not enough Gold!")

    db.update_player_resources(telegram_id, gold_delta=-selected_item["price"])
    if not db.get_inventory(telegram_id):
        db.create_inventory(telegram_id)
    db.add_to_inventory(telegram_id, selected_item['id'])

    await update.message.reply_text(f"👵️ You secretly purchased {selected_item['name']}! It's now in your inventory. 🤫")

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("\U0001F3AF Usage: /use <item_id>")

    item_id = context.args[0].lower()

    if not db.has_item(telegram_id, item_id):
        return await update.message.reply_text("\u274c You don't own this item!")

    if item_id == "basicshield":
        player = db.get_player_data(telegram_id)
        if player["ShieldActive"] == "Yes":
            return await update.message.reply_text("\U0001F6E1️ You already have a shield active!")
        db.player_profile.update_cell(db.find_player(telegram_id), 9, "Yes")
        await update.message.reply_text("\U0001F6E1️ Basic Shield activated! You're protected for 24 hours.")

    elif item_id == "revivekit":
        await update.message.reply_text("\U0001F6E0️ Revive Kit used! (Troop revive coming soon...)")

    elif item_id == "infinityscout":
        await update.message.reply_text("\U0001F6F8 Infinity Scout launched! (Spying coming soon...)")

    elif item_id == "hazmatdrone":
        await update.message.reply_text("\u2623️ Hazmat Drone deployed! (Radiation zones coming soon...)")

    elif item_id == "empdevice":
        await update.message.reply_text("\U0001F50C EMP Device activated! (Enemy shield disruption coming soon...)")

    else:
        return await update.message.reply_text("\u2753 Unknown item or feature not available yet!")

    db.use_from_inventory(telegram_id, item_id)  # ✅ Correctly consume item after using
